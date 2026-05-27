example = {}


with open("./localtest.sql", "r") as file:
    for line in file:
        # Extrahiere die ID nach "update" oder "create"
        id_match = line.find("update") != -1 or line.find("create") != -1
        id_start = line.find("update") if line.find("update") != -1 else line.find("create")
        id_end = line.find(" ", id_start) if id_start != -1 else None
        id = line[id_start:id_end].strip()

        model = None
        # Extrahiere den Modellwert
        model_start = line.find('"model":')
        if model_start != -1:

            update = line.find('update')
            parts = line.split()
            id = parts[6]
            model = line.split("model\": \"")[1].split("\"")[0]
            example[id] = model

print(example)
