#!/bin/sh

# config file format can be found in https://github.com/abetlen/llama-cpp-python/pull/931
python3 -m llama_cpp.server --config_file config.json
