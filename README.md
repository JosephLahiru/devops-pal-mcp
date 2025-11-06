# DevOps Guild Demo

## Locally Running LLMs Using Ollama and Docker.

- About me.
- Why local LLMs.
  > Local LLMs offer greater privacy, faster response times, offline access, 
  and full control over customization, making them ideal for secure, real-time, 
  and domain-specific applications without relying on external cloud services.
- Benefits of Local LLMs.
  - Data Privacy & Control
  - Reduced Latency
  - Customization
  - Offline Availability
  - Reliability
  - Less Censorship
- Greatest dream of an Engineer. (JARVIS)
  > - Ever wondered to build a system like JARVIS from IronMan?
  > - Ever wondered if JARVIS was cloudbased what type of issues will Tony face?
  > - Internet Down? Region Down? High Network Traffic?
- What is Ollama.
  > Ollama is a free and open source platform that allows you to run large language models (LLMs) 
  locally on your machine without relying on cloud APIs or external servers. 
  It’s designed to make LLMs accessible, secure, and customizable for developers, researchers, and enterprises.
- Required Specs.
  - CPU
    - Minimum: 4 cores
    - Recommended: 8 cores for larger models
    - Modern CPU with AVX512 support preferred
  - GPU (Optional but Recommended)
    - Nvidia GPU (More Tokens per Second): 8GB VRAM
  - Memory (RAM)
    - Base requirement: 8GB for 3B models
    - 16GB for 7B models
    - 32GB for 13B models
  - Storage
    - Minimum: 12GB for base installation
    - Recommended: 50GB total space
- Demo.
  - Intro on how MCP server and client works.
  - Run MCP with Ollama. (DevOps Pal)
  - Keep the MCP for docker commands only.
  - How to create a simple tool.
  - References.

## References

- [Docker Python library](https://docker-py.readthedocs.io/en/stable/)
- [Ollama Python library](https://github.com/ollama/ollama-python)
- [MCP Python library](https://github.com/modelcontextprotocol/python-sdk)
