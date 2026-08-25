import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"

MODELS_TO_TEST = [
    ("groq", "Groq"),
    ("mistral", "Mistral AI"),
    ("openrouter", "OpenRouter"),
    ("gemini", "Google Gemini"),
]


async def test_all_individual_models():
    print("🔬 Testing EACH Individual Model Separately (Direct Model Selection)...\n")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        for model_key, display_name in MODELS_TO_TEST:
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"🤖 Testing Provider: {display_name} (model='{model_key}')...")

            # 1. Create a fresh session and verify it
            init_res = await client.post("/chat", json={"message": f"Hello from {display_name} test"})
            session_id = init_res.json()["session_id"]
            
            # Verify identity
            await client.post("/chat/verify", json={
                "session_id": session_id,
                "answer": "Jamirah Najjemba"
            })

            # 2. Send prompt directly to this specific model
            res = await client.post("/chat", json={
                "session_id": session_id,
                "message": f"Say 'Hello Fred! I am {display_name} and I am working perfectly.' and give 1 short tip on FastAPI performance.",
                "model": model_key
            })

            if res.status_code == 200:
                data = res.json()
                print(f"   ✅ SUCCESS! Responded By: [{data['responded_by']}]")
                # Print clean snippet of the response
                content_preview = data["content"][:220].replace("\n", " ")
                print(f"   💬 Response: \"{content_preview}...\"\n")
            else:
                print(f"   ❌ FAILED for {display_name}: HTTP {res.status_code} - {res.text}\n")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🎉 ALL INDIVIDUAL MODEL TESTS COMPLETED!")


if __name__ == "__main__":
    asyncio.run(test_all_individual_models())
