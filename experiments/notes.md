# Experiments

I created an initial suite of 35 crude programmatic evals. The model could score multiple points by having expected words or strings in the response.

## Model info

```sh
❯ ollama show llama3.2
  Model
    architecture        llama     
    parameters          3.2B      
    context length      131072    
    embedding length    3072      
    quantization        Q4_K_M    

  Parameters
    stop    "<|start_header_id|>"    
    stop    "<|end_header_id|>"      
    stop    "<|eot_id|>"             

  License
    LLAMA 3.2 COMMUNITY LICENSE AGREEMENT                 
    Llama 3.2 Version Release Date: September 25, 2024
```

Without help, the model got: Score: 30/58 = 51.72%. The most common issue was refusal, which is annoying. Better prompting and better scoring to accept equivalents like "angiotensin-converting enzyme inhibitors" or "ACE inhibitors" quickly brought that score up.

Score: 30/58 = 51.72%
Score: 34/58 = 58.62%
Score: 41/58 = 70.69%
Score: 44/56 = 78.57%
