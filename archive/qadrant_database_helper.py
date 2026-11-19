
def load_in_memory():


# eGPUs solutition
# import torch
# print(torch.cuda.is_available())
#batch_vectors = model.encode(
#    batch_texts,
#    batch_size=64,        #  größer als CPU
#    show_progress_bar=False,
#    convert_to_numpy=True
#)

"""
BATCH_SIZE = 512

texts = df["text"].to_list()

for i in range(0, len(texts), BATCH_SIZE):
    batch_texts = texts[i:i + BATCH_SIZE]

    # ⚡ GPU Encoding
    batch_vectors = model.encode(
        batch_texts,
        batch_size=64,
        convert_to_numpy=True
    )

    points = [
        PointStruct(
            id=i + j,
            vector=batch_vectors[j],
            payload={"text": batch_texts[j]}
        )
        for j in range(len(batch_texts))
    ]

    client.upsert(collection_name="words", points=points)
"""
