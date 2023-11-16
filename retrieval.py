import openai
import json
from dotenv import load_dotenv
import vecs
import requests

load_dotenv()

from openai import OpenAI
import boto3
from pydub import AudioSegment


def download_file_from_s3(bucket_name, s3_object_key, local_file_name):
    s3 = boto3.client("s3")
    s3.download_file(bucket_name, s3_object_key, local_file_name)


def trim_audio(file_name, start_time_ms, end_time_ms, output_file_name):
    audio = AudioSegment.from_mp3(file_name)
    trimmed_audio = audio[start_time_ms:end_time_ms]
    trimmed_audio.export(output_file_name, format="mp3")


client = OpenAI()


class RetrievalInterface:
    def store(self, key, metadata):
        raise NotImplementedError

    def retrieve(self, key):
        raise NotImplementedError


class RetrievalDB(RetrievalInterface):
    def __init__(self, song_list=set()):
        # DB_CONNECTION = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        DB_CONNECTION = "postgresql://postgres:qeQ.xnvnGPGrdTt6f@db.pieozopknpjipisrgipw.supabase.co:5432/postgres"
        vx = vecs.create_client(DB_CONNECTION)
        # self.docs = vx.get_or_create_collection(
        #     name="taylor", dimension=1536
        # )  # random 1
        self.docs = vx.get_or_create_collection(
            name="taylor1_3456all_index", dimension=1536
        )  # random 3456
        self.count = 0
        self.song_list = song_list

    def _get_embedding(self, text, model="text-embedding-ada-002"):
        text = text.replace("\n", " ")
        return client.embeddings.create(input=[text], model=model).data[0].embedding

    def store(self, key, metadata):
        self.docs.upsert(
            [(str(self.count), self._get_embedding(key), {**metadata, "text": key})]
        )
        for i, value in metadata.items():
            self.song_list.add(value["name"])

        self.count += 1

    def create_index(self):
        self.docs.create_index()

    def _get_gpt_therapy_reply(self, key):
        PROMPT_MESSAGES = [
            {
                "role": "system",
                "content": f"""You are Taylor Swift and you only talk in your own song's lyrics. Your goal is to make your best friend feel better. Reply in Taylor Swift's songs' lyrics. Only reply with lyrics from songs that exist in this list: {list(self.song_list)}.""",
                # "content": f"""You are Taylor Swift and you only talk in your own song's lyrics. Your goal is to make your best friend feel better. Reply in Taylor Swift's songs' lyrics. Only reply with lyrics from songs that exist in this list: {list(self.song_list)}. You can chain lyrics from multiple songs, but delimit it by ;""",
            },
            {
                "role": "user",
                "content": f"""User: {key}""",
            },
            {
                "role": "assistant",
                "content": """Answer: """,
            },
        ]
        result = client.chat.completions.create(
            messages=PROMPT_MESSAGES,
            model="gpt-4-1106-preview",
            max_tokens=800,
        )
        content = result.choices[0].message.content
        print(f"GPT result is: {content}")

        closest = self.docs.query(
            data=self._get_embedding(content), limit=1, include_metadata=True
        )
        print(f"Closest result from after GPT is: {closest}")
        return closest

    def _get_closest_result_from_key(self, key):
        closest = self.docs.query(
            data=self._get_embedding(key), limit=1, include_metadata=True
        )
        print(f"Closest result from key {key} is: {closest}")
        return closest

    def retrieve(self, key):
        gpt_closest = self._get_closest_result_from_key(key)
        question_closet = self._get_gpt_therapy_reply(key)
        PROMPT_MESSAGES = [
            {
                "role": "system",
                "content": f"""You are a loving friend, which one of the replies is better to the users' complaint? 
                    {gpt_closest} 
                    AND 
                    {question_closet}; Just reply with the better one.""",
                # "content": f"""You are Taylor Swift and you only talk in your own song's lyrics. Your goal is to make your best friend feel better. Reply in Taylor Swift's songs' lyrics. Only reply with lyrics from songs that exist in this list: {list(self.song_list)}. You can chain lyrics from multiple songs, but delimit it by ;""",
            },
            {
                "role": "user",
                "content": f"""User: {key}""",
            },
            {
                "role": "assistant",
                "content": """Answer: """,
            },
        ]
        result = client.chat.completions.create(
            messages=PROMPT_MESSAGES,
            model="gpt-4-1106-preview",
            max_tokens=800,
        )
        content = result.choices[0].message.content
        print(f"GPT result is: {content}")

        # closests = []
        # splits = content.split(";")
        # for split in splits:
        closest = self.docs.query(
            data=self._get_embedding(content), limit=1, include_metadata=True
        )
        # closests.append(closest)
        print(f"Final closest result from list: {closest[0][1]['text']}")
        return closest[0][1]["text"]


class RetrievalGPT(RetrievalInterface):
    prompt2 = """
        {{#system~}}You are the best friend of a person who is telling you about their life, reply to make the person feel heard or reply to offer a suggestion or advice.{{~/system}}
        {{#user~}}
            User input: {{query}}
        {{~/user}}
        {{#assistant~}}{{gen 'answers' temperature=0 max_tokens=300}}{{~/assistant}}
    """

    def __init__(self):
        self.gpt = {}

    def store(self, key, metadata):
        self.gpt[key] = metadata

    def retrieve(self, key):
        options = ";".join(list(self.gpt.keys()))
        PROMPT_MESSAGES = [
            {
                "role": "system",
                "content": f"""You are the best friend of a person who is telling you about their life. Your goal is to echo their sentiment to make them feel heard. Please select response from this list (delimited by ;) and nothing else : {options}""",
            },
            {
                "role": "user",
                "content": f"""User input: {key}""",
            },
            {
                "role": "assistant",
                "content": """Answer: """,
            },
        ]
        result = client.chat.completions.create(
            messages=PROMPT_MESSAGES,
            model="gpt-4-1106-preview",
            max_tokens=800,
        )
        return result


# def get_sound_clips(clips):
#     # clip is of format: url, start, end
#     song_list = set()
#     for v in results_dict.values():
#         for song in v:
#             song_list.add(song["name"])

#     return song_list


def combine_results(results_dict):
    import random

    new_dict = {}
    for key, value in results_dict.items():
        for item in value:
            song_name = item["name"]
            if song_name not in new_dict:
                new_dict[song_name] = []
            new_dict[song_name].append(
                (item["timestamp"][0], key, item["timestamp"][1], item["url"])
            )

    brand_new_dict = {}
    for key, value in new_dict.items():
        value.sort()
        i = 0
        for n in [3, 4, 5, 6]:
            while i < len(value):
                text = " ".join([value[j][1] for j in range(i, min(i + n, len(value)))])
                start = value[i][0]
                end = value[min(i + n, len(value)) - 1][2]
                url = value[i][3]
                if text not in brand_new_dict:
                    brand_new_dict[text] = []
                brand_new_dict[text].append(
                    {"timestamp": [start, end], "url": url, "name": key}
                )
                i += n
    return brand_new_dict


with open("taylor1.json", "r") as f:
    results_dict = json.load(f)
    aggregate_results = combine_results(results_dict)

song_list = set()
for v in aggregate_results.values():
    for song in v:
        song_list.add(song["name"])

# retrieval_system = RetrievalGPT()
retrieval_system = RetrievalDB(song_list)
# for result, value in aggregate_results.items():
#     retrieval_system.store(result, {i: v for i, v in enumerate(value)})

# retrieval_system.create_index()

# rets = retrieval_system.retrieve(
#     "Why does everyone hate me? Please help me feel better."
# )
# rets = retrieval_system.retrieve("I have not exercised today. Help me feel better.")
# rets = retrieval_system.retrieve("Everyone hates me. Help me feel better.")
# rets = retrieval_system.retrieve("My boyfriend betrayed me.")
rets = retrieval_system.retrieve("Nobody invited me to their thanksgiving party.")
print(rets)

# 2g
values = aggregate_results[rets]
if len(values) > 0:
    url = values[0]["url"]
    start = values[0]["timestamp"][0]
    end = values[0]["timestamp"][1]
    response = requests.get(url)
    with open("output.mp3", "wb") as file:
        file.write(response.content)
        # Load the downloaded file

    audio = AudioSegment.from_mp3("output.mp3")
    # Cut the audio from the start time to the end
    if end is None:
        cut_audio = audio[start * 1000 :]
    else:
        cut_audio = audio[start * 1000 : end * 1000]
    # Export the cut audio
    cut_audio.export("cut_output.mp3", format="mp3")

print(f"DONE")
