import { describe, expect, it } from "vitest";

import { modelDisplayLabels, shortenModelName } from "./model-display.js";

describe("shortenModelName", () => {
  it("removes host, vendor, quantisation and tag noise", () => {
    expect(shortenModelName("LLM3.openai/gpt-oss-120b-GGUF")).toBe("gpt-oss-120b");
    expect(shortenModelName("LLM1-A40.meta-llama/Llama-3.3-70B-Instruct:UD-Q8_K_XL"))
      .toBe("Llama-3.3-70B-Instruct");
    expect(shortenModelName("mlx-community/Mistral-7B-Instruct-int4")).toBe("Mistral-7B-Instruct");
    expect(shortenModelName("google/gemini-3.7-flash:latest")).toBe("gemini-3.7-flash");
    expect(shortenModelName("openai/gpt-oss-120b-GGUF:latest")).toBe("gpt-oss-120b");
    expect(shortenModelName("mlx-community/Nemotron-30B-MLX-MXFP4")).toBe("Nemotron-30B");
    expect(shortenModelName("MAC2.mlx-community--NVIDIA-Nemotron-3-Nano-30B-A3B-MLX-MXFP4"))
      .toBe("NVIDIA-Nemotron-3-Nano-30B-A3B");
    expect(shortenModelName("MAC9.mlx-comunity--Example-7B-MLX-int4")).toBe("Example-7B");
  });

  it("keeps size and variant markers", () => {
    expect(shortenModelName("unsloth/gpt-oss-120b-Instruct-GGUF")).toBe("gpt-oss-120b-Instruct");
  });

  it("uses an explicit label for the OpenRouter free router", () => {
    expect(shortenModelName("openrouter/free")).toBe("OpenRouter Free");
  });

  it("is total for empty and unfamiliar discovered names", () => {
    expect(shortenModelName("")).toBe("");
    expect(shortenModelName("vendor/new-model.experimental")).toBe("vendor/new-model.experimental");
  });
});

describe("modelDisplayLabels", () => {
  it("falls back to both full names when compact labels collide", () => {
    expect(modelDisplayLabels(["openai/shared-7B", "meta-llama/shared-7B", "google/unique-model"]))
      .toEqual(["openai/shared-7B", "meta-llama/shared-7B", "unique-model"]);
  });
});
