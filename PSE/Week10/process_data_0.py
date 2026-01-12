def process_data(data):
    # step 1: Clean data
    cleaned_data = []
    for item in data:
        if isinstance(item, str):
            item = item.strip()
        cleaned_data.append(item)

    # step 2: Transform data
    transformed_data = []
    for item in cleaned_data:
        if isinstance(item, str):
            item = item.upper()
        transformed_data.append(item)

    # step 3: Summarize data
    summary = {}
    for item in transformed_data:
        if item in summary:
            summary[item] += 1
        else:
            summary[item] = 1

    return summary