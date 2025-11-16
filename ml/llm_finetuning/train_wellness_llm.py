"""
Fine-tune Llama-2-7B for Wellness Coaching using QLoRA.

This script implements efficient fine-tuning using:
- QLoRA (Quantized Low-Rank Adaptation)
- 4-bit quantization for memory efficiency
- LoRA adapters for parameter-efficient training
- Custom wellness Q&A dataset

Runs on single RTX 3060 (12GB VRAM) or similar GPU.
"""

import os
import json
import torch
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List

import transformers
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    PeftModel,
)
from datasets import load_dataset, Dataset
import wandb

@dataclass
class ModelArguments:
    """Arguments for model configuration."""
    model_name_or_path: str = field(
        default="meta-llama/Llama-2-7b-hf",
        metadata={"help": "Path to pretrained model or model identifier from huggingface.co/models"}
    )
    use_4bit: bool = field(
        default=True,
        metadata={"help": "Activate 4bit precision base model loading"}
    )
    bnb_4bit_compute_dtype: str = field(
        default="float16",
        metadata={"help": "Compute dtype for 4bit base models"}
    )
    bnb_4bit_quant_type: str = field(
        default="nf4",
        metadata={"help": "Quantization type (fp4 or nf4)"}
    )
    use_nested_quant: bool = field(
        default=True,
        metadata={"help": "Activate nested quantization for 4bit base models"}
    )

@dataclass
class LoraArguments:
    """Arguments for LoRA configuration."""
    lora_r: int = field(
        default=64,
        metadata={"help": "Lora attention dimension"}
    )
    lora_alpha: int = field(
        default=16,
        metadata={"help": "Lora alpha parameter"}
    )
    lora_dropout: float = field(
        default=0.1,
        metadata={"help": "Lora dropout"}
    )
    lora_target_modules: List[str] = field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"],
        metadata={"help": "Target modules for LoRA"}
    )
    bias: str = field(
        default="none",
        metadata={"help": "Bias type for Lora"}
    )
    task_type: str = field(
        default="CAUSAL_LM",
        metadata={"help": "Task type"}
    )

@dataclass
class DataArguments:
    """Arguments for data configuration."""
    data_path: str = field(
        default="data/training/wellness_qa_complete.json",
        metadata={"help": "Path to training data"}
    )
    max_length: int = field(
        default=2048,
        metadata={"help": "Maximum sequence length"}
    )


class WellnessDataProcessor:
    """Process wellness Q&A data for instruction fine-tuning."""

    def __init__(self, tokenizer, max_length=2048):
        self.tokenizer = tokenizer
        self.max_length = max_length

    def create_prompt(self, instruction: str, input_text: str, output_text: str = None) -> str:
        """Create instruction-following prompt."""

        # Alpaca-style prompt format
        prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input_text}

### Response:
"""
        if output_text:
            prompt += output_text

        return prompt

    def tokenize_function(self, example):
        """Tokenize examples for training."""

        # Create full prompt with response
        full_prompt = self.create_prompt(
            example["instruction"],
            example["input"],
            example["output"]
        )

        # Tokenize
        tokenized = self.tokenizer(
            full_prompt,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors=None,
        )

        # Create labels (same as input_ids for causal LM)
        tokenized["labels"] = tokenized["input_ids"].copy()

        return tokenized

    def load_and_prepare_dataset(self, data_path: str):
        """Load and prepare dataset for training."""

        # Load from JSON
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert to HuggingFace Dataset
        dataset = Dataset.from_list(data)

        # Tokenize
        tokenized_dataset = dataset.map(
            self.tokenize_function,
            remove_columns=dataset.column_names,
            desc="Tokenizing dataset",
        )

        return tokenized_dataset


class WellnessLLMTrainer:
    """Trainer for wellness coaching LLM using QLoRA."""

    def __init__(
        self,
        model_args: ModelArguments,
        lora_args: LoraArguments,
        data_args: DataArguments,
        training_args: TrainingArguments,
    ):
        self.model_args = model_args
        self.lora_args = lora_args
        self.data_args = data_args
        self.training_args = training_args

        self.model = None
        self.tokenizer = None
        self.dataset = None

    def setup_model_and_tokenizer(self):
        """Initialize model and tokenizer with quantization."""

        print("🔧 Setting up model and tokenizer...")

        # Quantization configuration
        compute_dtype = getattr(torch, self.model_args.bnb_4bit_compute_dtype)

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=self.model_args.use_4bit,
            bnb_4bit_quant_type=self.model_args.bnb_4bit_quant_type,
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=self.model_args.use_nested_quant,
        )

        # Load base model
        print(f"📥 Loading base model: {self.model_args.model_name_or_path}")
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_args.model_name_or_path,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )

        # Disable cache for gradient checkpointing
        self.model.config.use_cache = False
        self.model.config.pretraining_tp = 1

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_args.model_name_or_path,
            trust_remote_code=True
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"

        print("✅ Model and tokenizer loaded successfully")

    def setup_lora(self):
        """Configure and apply LoRA adapters."""

        print("🔧 Configuring LoRA...")

        # Prepare model for k-bit training
        self.model = prepare_model_for_kbit_training(self.model)

        # LoRA configuration
        lora_config = LoraConfig(
            r=self.lora_args.lora_r,
            lora_alpha=self.lora_args.lora_alpha,
            target_modules=self.lora_args.lora_target_modules,
            lora_dropout=self.lora_args.lora_dropout,
            bias=self.lora_args.bias,
            task_type=self.lora_args.task_type,
        )

        # Apply LoRA
        self.model = get_peft_model(self.model, lora_config)

        # Print trainable parameters
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.model.parameters())

        print(f"✅ LoRA applied successfully")
        print(f"📊 Trainable params: {trainable_params:,} ({100 * trainable_params / total_params:.2f}%)")
        print(f"📊 Total params: {total_params:,}")

    def prepare_dataset(self):
        """Load and prepare training dataset."""

        print("📚 Preparing dataset...")

        processor = WellnessDataProcessor(
            self.tokenizer,
            max_length=self.data_args.max_length
        )

        self.dataset = processor.load_and_prepare_dataset(self.data_args.data_path)

        # Split into train/validation
        dataset_split = self.dataset.train_test_split(test_size=0.1, seed=42)
        self.train_dataset = dataset_split["train"]
        self.eval_dataset = dataset_split["test"]

        print(f"✅ Dataset prepared")
        print(f"📊 Training examples: {len(self.train_dataset)}")
        print(f"📊 Validation examples: {len(self.eval_dataset)}")

    def train(self):
        """Execute fine-tuning."""

        print("🚀 Starting training...")

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,  # Causal LM, not masked
        )

        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=self.training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset,
            data_collator=data_collator,
        )

        # Train
        train_result = trainer.train()

        # Save metrics
        metrics = train_result.metrics
        trainer.log_metrics("train", metrics)
        trainer.save_metrics("train", metrics)

        print("✅ Training completed!")

        return trainer

    def save_model(self, output_dir: str):
        """Save fine-tuned model and tokenizer."""

        print(f"💾 Saving model to {output_dir}...")

        # Save LoRA adapters
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)

        print("✅ Model saved successfully!")


def main():
    """Main training function."""

    # Initialize wandb (optional)
    wandb.init(
        project="wellness-ai-llm",
        name="llama2-7b-qlora-wellness",
        config={
            "model": "Llama-2-7B",
            "method": "QLoRA",
            "task": "wellness-coaching",
        }
    )

    # Configuration
    model_args = ModelArguments(
        model_name_or_path="meta-llama/Llama-2-7b-hf",  # Change to local path if downloaded
        use_4bit=True,
        bnb_4bit_compute_dtype="float16",
        bnb_4bit_quant_type="nf4",
        use_nested_quant=True,
    )

    lora_args = LoraArguments(
        lora_r=64,
        lora_alpha=16,
        lora_dropout=0.1,
        lora_target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )

    data_args = DataArguments(
        data_path="data/training/wellness_qa_complete.json",
        max_length=2048,
    )

    training_args = TrainingArguments(
        output_dir="models/wellness-llama2-7b-qlora",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        gradient_accumulation_steps=4,
        gradient_checkpointing=True,
        optim="paged_adamw_32bit",
        save_steps=50,
        logging_steps=10,
        learning_rate=2e-4,
        weight_decay=0.001,
        fp16=True,
        bf16=False,
        max_grad_norm=0.3,
        max_steps=-1,
        warmup_ratio=0.03,
        group_by_length=True,
        lr_scheduler_type="cosine",
        report_to="wandb",
        evaluation_strategy="steps",
        eval_steps=50,
        save_total_limit=3,
        load_best_model_at_end=True,
    )

    # Initialize trainer
    trainer_wrapper = WellnessLLMTrainer(
        model_args=model_args,
        lora_args=lora_args,
        data_args=data_args,
        training_args=training_args,
    )

    # Setup
    trainer_wrapper.setup_model_and_tokenizer()
    trainer_wrapper.setup_lora()
    trainer_wrapper.prepare_dataset()

    # Train
    trainer = trainer_wrapper.train()

    # Save
    trainer_wrapper.save_model("models/wellness-llama2-7b-qlora-final")

    # Evaluate
    print("\n📊 Final Evaluation:")
    eval_results = trainer.evaluate()
    print(eval_results)

    wandb.finish()
    print("\n🎉 Training pipeline completed successfully!")


if __name__ == "__main__":
    main()
