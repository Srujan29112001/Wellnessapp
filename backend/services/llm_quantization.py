"""
LLM Quantization and LoRA Implementation
Efficient model inference using quantization and LoRA fine-tuning
"""

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    PeftModel
)
import logging
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class QuantizedLLM:
    """
    Quantized LLM with LoRA for efficient inference

    Uses 4-bit quantization (QLoRA) to run large models on limited GPU memory
    """

    def __init__(
        self,
        model_name: str = "meta-llama/Llama-2-7b-chat-hf",
        use_4bit: bool = True,
        use_lora: bool = True,
        lora_rank: int = 16,
        lora_alpha: int = 32,
    ):
        """
        Initialize quantized LLM

        Args:
            model_name: HuggingFace model name
            use_4bit: Use 4-bit quantization
            use_lora: Use LoRA adapters
            lora_rank: LoRA rank (lower = more compression)
            lora_alpha: LoRA alpha scaling
        """
        self.model_name = model_name
        self.use_4bit = use_4bit
        self.use_lora = use_lora

        # Configure quantization
        if use_4bit:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",  # Normal Float 4
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,  # Nested quantization
            )
            logger.info("Using 4-bit quantization (QLoRA)")
        else:
            bnb_config = None
            logger.info("Loading model without quantization")

        # Load model
        logger.info(f"Loading model: {model_name}")
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config if use_4bit else None,
            device_map="auto",  # Automatic device placement
            trust_remote_code=True,
            torch_dtype=torch.float16,
        )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token

        # Apply LoRA if enabled
        if use_lora:
            lora_config = LoraConfig(
                r=lora_rank,  # Rank of update matrices
                lora_alpha=lora_alpha,  # Scaling factor
                target_modules=["q_proj", "v_proj"],  # Which layers to apply LoRA
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM"
            )

            # Prepare model for k-bit training
            if use_4bit:
                self.model = prepare_model_for_kbit_training(self.model)

            # Get PEFT model
            self.model = get_peft_model(self.model, lora_config)
            self.model.print_trainable_parameters()

            logger.info(f"Applied LoRA with rank={lora_rank}, alpha={lora_alpha}")

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """
        Generate text from prompt

        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold

        Returns:
            Generated text
        """
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove prompt from output
        generated_text = generated_text[len(prompt):].strip()

        return generated_text

    def save_lora_weights(self, save_path: str):
        """Save LoRA adapter weights (not the full model)"""
        if self.use_lora:
            self.model.save_pretrained(save_path)
            logger.info(f"LoRA weights saved to {save_path}")
        else:
            logger.warning("LoRA not enabled, nothing to save")

    @classmethod
    def load_from_lora_weights(
        cls,
        base_model_name: str,
        lora_weights_path: str
    ):
        """Load model with pretrained LoRA weights"""
        logger.info(f"Loading LoRA weights from {lora_weights_path}")

        # Load base model with quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
        )

        # Load LoRA adapters
        model = PeftModel.from_pretrained(base_model, lora_weights_path)

        # Create instance
        instance = cls.__new__(cls)
        instance.model = model
        instance.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        instance.use_4bit = True
        instance.use_lora = True

        logger.info("Model loaded successfully with LoRA weights")

        return instance

    def get_model_size_mb(self) -> float:
        """Get approximate model size in memory"""
        param_size = sum(p.nelement() * p.element_size() for p in self.model.parameters())
        buffer_size = sum(b.nelement() * b.element_size() for b in self.model.buffers())
        size_mb = (param_size + buffer_size) / (1024 ** 2)
        return size_mb


def compare_model_sizes():
    """Compare model sizes with and without quantization"""
    print("Comparing model sizes...")

    # Full precision (would need ~13GB for 7B model)
    print("Full FP16 model: ~13GB")

    # With 4-bit quantization
    print("4-bit quantized: ~3.5GB (73% reduction)")

    # With LoRA on top
    print("4-bit + LoRA adapters: ~3.5GB + ~10MB for adapters")


# Example usage
def create_wellness_coach_llm(
    model_name: str = "meta-llama/Llama-2-7b-chat-hf",
    lora_weights_path: Optional[str] = None
) -> QuantizedLLM:
    """
    Create a wellness coach LLM with quantization

    Args:
        model_name: Base model name
        lora_weights_path: Optional path to fine-tuned LoRA weights

    Returns:
        Quantized LLM instance
    """
    if lora_weights_path and Path(lora_weights_path).exists():
        # Load with fine-tuned LoRA weights
        llm = QuantizedLLM.load_from_lora_weights(model_name, lora_weights_path)
    else:
        # Create new quantized model
        llm = QuantizedLLM(
            model_name=model_name,
            use_4bit=True,
            use_lora=True,
            lora_rank=16,
            lora_alpha=32
        )

    logger.info(f"Model size in memory: {llm.get_model_size_mb():.2f} MB")

    return llm
