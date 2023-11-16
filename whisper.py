import fal
import json
from dotenv import load_dotenv

load_dotenv()


def print_json():
    print(f"printing json")
    with open("taylor4.json", "w") as json_file:
        json.dump(results, json_file)


with open("metadata2_reformatted.txt", "r") as file:
    data = file.readlines()

metadata = []
for line in data:
    print(line)
    url_and_rest = line.strip().split(", ")
    metadata.append((url_and_rest[0][:-4], ", ".join(url_and_rest[1:])))


results = {}
count = 0
for url, name in metadata[100:]:
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
            results[chunk["text"]] = [
                {
                    "timestamp": chunk["timestamp"],
                    "url": url,
                    "name": name,
                }
            ]
        else:
            results[chunk["text"]].append(
                {
                    "timestamp": chunk["timestamp"],
                    "url": url,
                    "name": name,
                }
            )
            print(
                f"Repeat found - text:{chunk['text']} between {', '.join([a['name'] for a in results[chunk['text']]])} and {name}"
            )

    count += 1
    if count % 20 == 0:
        print_json()

print(results)
print_json()

# results[name] = result
# print(f"Result for {name}: {result}")
