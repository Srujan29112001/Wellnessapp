# Wellness LLM Fine-tuning with QLoRA

This directory contains everything needed to fine-tune Llama-2-7B for holistic wellness coaching using QLoRA (Quantized Low-Rank Adaptation).

## Overview

**Goal**: Create a privacy-preserving, locally-runnable LLM specialized in holistic wellness coaching.

**Method**: QLoRA fine-tuning on wellness Q&A dataset

**Base Model**: Llama-2-7B-hf

**Hardware Requirements**:
- GPU: NVIDIA RTX 3060 (12GB VRAM) or better
- RAM: 16GB+ system RAM
- Storage: 50GB for models and datasets

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Data

The training dataset is generated automatically:

```bash
python ../../scripts/generate_llm_training_data.py
```

This creates `data/training/wellness_qa_complete.json` with comprehensive wellness Q&A pairs covering:
- Stress and sleep management
- Nutrition and diet
- EEG interpretation
- Ayurvedic principles
- Supplement recommendations
- Mental health support

### 3. Download Base Model (Optional)

If you want to use a local model instead of downloading from HuggingFace:

```bash
# Using Hugging Face CLI
huggingface-cli download meta-llama/Llama-2-7b-hf --local-dir models/llama-2-7b-hf

# Or use transformers
python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('meta-llama/Llama-2-7b-hf', cache_dir='models/')"
```

**Note**: You need HuggingFace account access to Meta Llama models. Request access at: https://huggingface.co/meta-llama/Llama-2-7b-hf

### 4. Train the Model

```bash
# With wandb logging (recommended)
wandb login
python train_wellness_llm.py

# Without wandb
python train_wellness_llm.py --report_to none
```

**Training Time**:
- RTX 3060 (12GB): ~2-4 hours for 3 epochs
- RTX 4090 (24GB): ~1-2 hours for 3 epochs

**Memory Usage**:
- 4-bit quantization: ~8-10GB VRAM
- Full precision: ~28-30GB VRAM (requires A100)

### 5. Run Inference

```bash
# Demo mode (predefined examples)
python inference_wellness_llm.py

# Interactive chat
python inference_wellness_llm.py interactive
```

## Architecture Details

### QLoRA Configuration

**Quantization:**
- 4-bit NF4 quantization of base model
- FP16 compute dtype
- Nested quantization enabled

**LoRA Parameters:**
- Rank (r): 64
- Alpha: 16
- Dropout: 0.1
- Target modules: q_proj, k_proj, v_proj, o_proj

**Why these settings?**
- r=64: Higher rank for complex wellness domain knowledge
- Alpha=16: Lower than r for better generalization
- Dropout=0.1: Prevent overfitting on small dataset

### Training Configuration

```python
TrainingArguments(
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,  # Effective batch size = 16
    learning_rate=2e-4,
    fp16=True,
    optim="paged_adamw_32bit",
    lr_scheduler_type="cosine",
)
```

**Why these settings?**
- Small batch size: Memory constraints
- Gradient accumulation: Larger effective batch size
- LR=2e-4: Standard for QLoRA fine-tuning
- Cosine scheduler: Smooth learning rate decay

## Dataset Format

The training data follows the Alpaca instruction format:

```json
{
  "instruction": "You are a holistic wellness coach...",
  "input": "User's question or concern",
  "output": "Detailed, evidence-based response with actionable advice",
  "category": "stress_sleep | nutrition | eeg | ayurveda | supplements"
}
```

### Expanding the Dataset

To add more training examples:

1. Edit `scripts/generate_llm_training_data.py`
2. Add new Q&A pairs to relevant category lists
3. Regenerate dataset: `python scripts/generate_llm_training_data.py`
4. Retrain model

**Recommended dataset size**: 100-500 high-quality examples for domain specialization.

## Model Usage

### Basic Inference

```python
from inference_wellness_llm import WellnessLLMInference

# Initialize
llm = WellnessLLMInference(
    model_path="models/wellness-llama2-7b-qlora-final",
    load_in_4bit=True
)

# Generate response
result = llm.chat(
    user_query="I'm feeling stressed and can't sleep. What should I do?",
    user_context={
        "dosha": "Vata",
        "stress_level": 8,
        "sleep_hours": 4.5
    }
)

print(result['response'])
```

### Integration with Wellness Coach Service

```python
# backend/services/llm_coach_service.py

from ml.llm_finetuning.inference_wellness_llm import WellnessLLMInference

class WellnessCoach:
    def __init__(self):
        # Use fine-tuned local model instead of API
        self.local_llm = WellnessLLMInference(
            model_path="models/wellness-llama2-7b-qlora-final",
            load_in_4bit=True
        )

    def chat(self, user_id: str, message: str, db):
        # Get user context from database
        user = db.query(User).filter(User.id == user_id).first()
        context = {
            "dosha": user.dosha_type,
            "stress_level": user.last_stress_level,
            "sleep_hours": user.last_sleep_hours,
        }

        # Generate response using local LLM
        result = self.local_llm.chat(
            user_query=message,
            user_context=context,
            max_new_tokens=512,
            temperature=0.7
        )

        return result['response']
```

## Performance Optimization

### Memory Optimization

1. **Use smaller models**: Try Llama-2-7B-chat or Mistral-7B
2. **Reduce sequence length**: max_length=1024 instead of 2048
3. **Gradient checkpointing**: Already enabled
4. **Batch size**: Reduce if OOM errors

### Speed Optimization

1. **Flash Attention**: Install `flash-attn` for 2-4x speedup
2. **Better GPU**: RTX 4090 or A100 for faster training
3. **Mixed precision**: Use bf16 if supported (Ampere+ GPUs)
4. **vLLM serving**: Use vLLM for production inference (10x faster)

```bash
# Install vLLM for production serving
pip install vllm

# Serve model
vllm serve models/wellness-llama2-7b-qlora-final \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype half \
    --max-model-len 2048
```

## Evaluation

### Automated Metrics

The trainer automatically logs:
- Training loss
- Validation loss
- Perplexity

### Manual Evaluation

Use the evaluation script:

```bash
python evaluate_wellness_llm.py
```

This tests the model on held-out wellness questions and computes:
- Response quality (1-5 scale)
- Factual accuracy
- Empathy score
- Actionability

### Human Evaluation

1. Generate responses for 20-50 test queries
2. Have domain expert (nutritionist, wellness coach) rate:
   - Accuracy of information
   - Safety (no harmful advice)
   - Empathy and tone
   - Actionability
   - Cultural sensitivity (Ayurveda accuracy)

## Troubleshooting

### OOM (Out of Memory) Errors

```python
# Reduce batch size
per_device_train_batch_size=2
gradient_accumulation_steps=8

# Reduce sequence length
max_length=1024

# Use smaller LoRA rank
lora_r=32
```

### Model Not Learning

```python
# Increase learning rate
learning_rate=5e-4

# Increase LoRA rank
lora_r=128

# More epochs
num_train_epochs=5

# Check data quality
# - Ensure diverse examples
# - Verify formatting is correct
```

### Slow Training

```bash
# Install flash-attention
pip install flash-attn

# Use bf16 (if supported)
bf16=True
fp16=False

# Enable TF32 (Ampere+ GPUs)
export NVIDIA_TF32_OVERRIDE=1
```

### Base Model Download Issues

```bash
# Use mirrors
export HF_ENDPOINT=https://hf-mirror.com

# Or download manually and use local path
model_name_or_path="/path/to/local/llama-2-7b"
```

## Privacy & Security

### Why Local LLM?

1. **Patient Privacy**: Health data never leaves your server
2. **HIPAA Compliance**: Full data control
3. **No API Costs**: Unlimited inference
4. **Customization**: Fine-tune on proprietary data
5. **Reliability**: No dependency on external services

### Security Best Practices

1. **Model Access Control**: Restrict who can query the model
2. **Input Sanitization**: Validate and clean user inputs
3. **Output Filtering**: Remove any PII that might leak
4. **Audit Logging**: Log all queries and responses
5. **Regular Updates**: Retrain with new wellness research

## Production Deployment

### Option 1: FastAPI Service

```python
# backend/api/endpoints/local_llm.py

from fastapi import APIRouter
from ml.llm_finetuning.inference_wellness_llm import WellnessLLMInference

router = APIRouter()

# Load model once at startup
llm = WellnessLLMInference(
    model_path="models/wellness-llama2-7b-qlora-final",
    load_in_4bit=True
)

@router.post("/chat")
async def chat(user_query: str, context: dict = None):
    response = llm.chat(user_query, context)
    return response
```

### Option 2: vLLM Server (Recommended for Production)

```bash
# Start vLLM server
vllm serve models/wellness-llama2-7b-qlora-final \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype half \
    --gpu-memory-utilization 0.9
```

Then query via OpenAI-compatible API:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-used"
)

response = client.chat.completions.create(
    model="wellness-llama2-7b-qlora-final",
    messages=[
        {"role": "system", "content": "You are a holistic wellness coach..."},
        {"role": "user", "content": "I'm stressed and can't sleep"}
    ]
)
```

### Option 3: Docker Deployment

```dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Install dependencies
RUN pip install -r requirements.txt

# Copy model
COPY models/wellness-llama2-7b-qlora-final /app/model

# Run inference server
CMD ["python", "serve_llm.py"]
```

## Roadmap

### Near-term (1-2 weeks)
- [ ] Expand dataset to 100+ examples
- [ ] Add evaluation metrics
- [ ] Implement streaming responses
- [ ] Add conversation history support

### Medium-term (1-2 months)
- [ ] Fine-tune Mistral-7B for comparison
- [ ] Implement RAG integration
- [ ] Add few-shot learning examples
- [ ] Multi-language support

### Long-term (3+ months)
- [ ] Continual learning from user interactions
- [ ] Federated learning across deployments
- [ ] Speculative decoding for faster inference
- [ ] Fine-tune Llama-2-13B for better quality

## References

- [QLoRA Paper](https://arxiv.org/abs/2305.14314)
- [Llama 2 Paper](https://arxiv.org/abs/2307.09288)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [HuggingFace PEFT](https://huggingface.co/docs/peft)
- [bitsandbytes Quantization](https://github.com/TimDettmers/bitsandbytes)

## License

This fine-tuning code is MIT licensed. However, the base Llama-2 model follows Meta's license agreement.

## Support

For issues or questions:
1. Check this README
2. Review training logs in `models/wellness-llama2-7b-qlora/`
3. Consult HuggingFace documentation
4. Open an issue in the project repository
