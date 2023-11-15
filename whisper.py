import fal
import json
from dotenv import load_dotenv

load_dotenv()

with open("metadata.txt", "r") as file:
    data = file.readlines()

metadata = []
for line in data:
    url, name = line.strip().split(", ")
    metadata.append((url, name))


results = {}
for url, name in metadata:
    handler = fal.apps.submit(
        "110602490-whisper",
        arguments={"url": url},
    )

    for event in handler.iter_events():
        if isinstance(event, fal.apps.InProgress):
            print(f"Request for {name} in progress")
            print(event.logs)

    result = handler.get()
    for chunk in result["chunks"]:
        if chunk["text"] not in results:
            results[chunk["text"]] = {
                "timestamp": chunk["timestamp"],
                "url": url,
                "name": name,
            }
        else:
            print(
                f"Repeat found - text:{chunk['text']} between {results[chunk['text']]['name']} and {name}"
            )

print(results)
with open("results.json", "w") as json_file:
    json.dump(results, json_file)

    # results[name] = result
    # print(f"Result for {name}: {result}")
