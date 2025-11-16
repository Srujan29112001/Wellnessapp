"""
Inference pipeline for fine-tuned Wellness LLM.

Load and use the QLoRA fine-tuned Llama-2-7B model for wellness coaching.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel, PeftConfig
from typing import Optional, Dict
import warnings

warnings.filterwarnings('ignore')


class WellnessLLMInference:
    """Inference wrapper for wellness coaching LLM."""

    def __init__(
        self,
        model_path: str,
        base_model: str = "meta-llama/Llama-2-7b-hf",
        load_in_4bit: bool = True,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        """
        Initialize inference model.

        Args:
            model_path: Path to fine-tuned LoRA adapters
            base_model: Base model name or path
            load_in_4bit: Use 4-bit quantization for memory efficiency
            device: Device to load model on
        """
        self.model_path = model_path
        self.base_model = base_model
        self.load_in_4bit = load_in_4bit
        self.device = device

        self.model = None
        self.tokenizer = None

        self._load_model()

    def _load_model(self):
        """Load base model and LoRA adapters."""

        print(f"🔧 Loading model from {self.model_path}...")

        # Quantization config
        if self.load_in_4bit:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
        else:
            bnb_config = None

        # Load base model
        print(f"📥 Loading base model: {self.base_model}")
        base = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )

        # Load LoRA adapters
        print(f"📥 Loading LoRA adapters from: {self.model_path}")
        self.model = PeftModel.from_pretrained(base, self.model_path)
        self.model.eval()

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"

        print("✅ Model loaded successfully!")

    def create_prompt(self, user_query: str, context: Optional[str] = None) -> str:
        """Create formatted prompt for the model."""

        instruction = "You are a holistic wellness coach with expertise in Ayurveda, nutrition, mental health, and preventive healthcare. Provide evidence-based, empathetic, and actionable advice."

        if context:
            input_text = f"{context}\n\nUser Question: {user_query}"
        else:
            input_text = user_query

        prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input_text}

### Response:
"""
        return prompt

    def generate_response(
        self,
        user_query: str,
        context: Optional[str] = None,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.15,
    ) -> str:
        """
        Generate wellness coaching response.

        Args:
            user_query: User's question or concern
            context: Optional context (user history, EEG data, etc.)
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (higher = more creative)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            repetition_penalty: Penalty for repetition

        Returns:
            Generated response
        """

        # Create prompt
        prompt = self.create_prompt(user_query, context)

        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(self.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Decode
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract only the generated response (after "### Response:")
        if "### Response:" in full_response:
            response = full_response.split("### Response:")[-1].strip()
        else:
            response = full_response

        return response

    def chat(
        self,
        user_query: str,
        user_context: Optional[Dict] = None,
        **generation_kwargs
    ) -> Dict[str, str]:
        """
        High-level chat interface.

        Args:
            user_query: User's message
            user_context: Dictionary with user info (dosha, recent EEG, etc.)
            **generation_kwargs: Additional generation parameters

        Returns:
            Dictionary with response and metadata
        """

        # Format context if provided
        context_str = None
        if user_context:
            context_parts = []
            if "dosha" in user_context:
                context_parts.append(f"User's Ayurvedic dosha: {user_context['dosha']}")
            if "recent_eeg" in user_context:
                context_parts.append(f"Recent EEG analysis: {user_context['recent_eeg']}")
            if "stress_level" in user_context:
                context_parts.append(f"Current stress level: {user_context['stress_level']}/10")
            if "sleep_hours" in user_context:
                context_parts.append(f"Last night sleep: {user_context['sleep_hours']} hours")

            if context_parts:
                context_str = "\n".join(context_parts)

        # Generate response
        response = self.generate_response(
            user_query,
            context=context_str,
            **generation_kwargs
        )

        return {
            "query": user_query,
            "response": response,
            "context": context_str,
        }


def demo_inference():
    """Demo usage of the fine-tuned model."""

    print("=== Wellness LLM Inference Demo ===\n")

    # Initialize model
    # NOTE: Update model_path to your trained model location
    model_path = "models/wellness-llama2-7b-qlora-final"

    try:
        llm = WellnessLLMInference(
            model_path=model_path,
            base_model="meta-llama/Llama-2-7b-hf",
            load_in_4bit=True
        )
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("\n💡 Make sure you've:")
        print("  1. Fine-tuned the model using train_wellness_llm.py")
        print("  2. Downloaded Llama-2-7B base model")
        print("  3. Set correct paths in the script")
        return

    # Example queries
    examples = [
        {
            "query": "I'm feeling very stressed and can't sleep. What should I do?",
            "context": {
                "dosha": "Vata",
                "stress_level": 8,
                "sleep_hours": 4.5
            }
        },
        {
            "query": "My EEG shows high beta waves. What does this mean?",
            "context": {
                "recent_eeg": "High beta (70%), low alpha (15%)"
            }
        },
        {
            "query": "What supplements should I take for better focus?",
            "context": {
                "dosha": "Pitta"
            }
        }
    ]

    # Run examples
    for i, example in enumerate(examples, 1):
        print(f"\n{'='*60}")
        print(f"Example {i}:")
        print(f"{'='*60}")
        print(f"\n👤 User: {example['query']}")

        if example.get('context'):
            print(f"\n📊 Context: {example['context']}")

        result = llm.chat(
            user_query=example['query'],
            user_context=example.get('context'),
            max_new_tokens=512,
            temperature=0.7
        )

        print(f"\n🤖 AI Coach:\n{result['response']}")

    print(f"\n{'='*60}")
    print("✅ Demo completed!")


def interactive_chat():
    """Interactive chat session with the model."""

    print("=== Interactive Wellness Coach ===\n")

    # Initialize model
    model_path = "models/wellness-llama2-7b-qlora-final"

    try:
        llm = WellnessLLMInference(model_path=model_path, load_in_4bit=True)
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    print("\n💬 Chat with your AI wellness coach!")
    print("Type 'quit' to exit, 'context' to add user context\n")

    user_context = {}

    while True:
        user_input = input("\n👤 You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == 'quit':
            print("\n👋 Thank you for using Wellness AI Coach!")
            break

        if user_input.lower() == 'context':
            print("\n📊 Add context (press Enter to skip):")
            dosha = input("  Dosha (Vata/Pitta/Kapha): ").strip()
            stress = input("  Stress level (1-10): ").strip()
            sleep = input("  Last night sleep (hours): ").strip()

            user_context = {}
            if dosha:
                user_context["dosha"] = dosha
            if stress:
                user_context["stress_level"] = stress
            if sleep:
                user_context["sleep_hours"] = sleep

            print("\n✅ Context updated!")
            continue

        # Generate response
        print("\n🤖 AI Coach: ", end="", flush=True)
        result = llm.chat(user_query=user_input, user_context=user_context)
        print(result['response'])


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_chat()
    else:
        demo_inference()
