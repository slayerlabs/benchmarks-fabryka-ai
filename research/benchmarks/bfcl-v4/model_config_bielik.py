

# Bielik 11B v3.1 Instruct served by vLLM (served-model-name "bielik"), appended by run.sh.
MODEL_CONFIG_MAPPING["bielik-FC"] = ModelConfig(
    model_name="bielik",
    display_name="Bielik-11B-v3.1-Instruct (FC)",
    url="https://huggingface.co/speakleash/Bielik-11B-v3.1-Instruct",
    org="SpeakLeash & ACK Cyfronet AGH",
    license="Apache 2.0",
    model_handler=OpenAICompletionsHandler,
    is_fc_model=True,
    underscore_to_dot=True,
)
