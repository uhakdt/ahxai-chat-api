def serialize_content(content):
    if content.type == "text":
        return {
            "type": content.type,
            "text": {
                "value": content.text.value,
            }
        }
    elif content.type == "image_file":
        return {
            "type": content.type,
            "image_file": {
                "file_id": content.image_file.file_id,
            }
        }
    elif content.type == "image_url":
        return {
            "type": content.type,
            "image_url": {
                "url": content.image_url.url,
            }
        }
    return content

def retrieve_message(client, thread_id, message_id):
    try:
        message = client.beta.threads.messages.retrieve(
            thread_id=thread_id,
            message_id=message_id
        )
        return {
            "id": message.id,
            "created_at": message.created_at,
            "thread_id": message.thread_id,
            "role": message.role,
            "content": [serialize_content(c) for c in message.content],
            "assistant_id": message.assistant_id,
            "run_id": message.run_id,
        }
    except Exception as e:
        return {"error": str(e)}

def serialize_run_step(client, step):
    step_dict = {
        "id": step.id,
        "created_at": step.created_at,
    }

    # Add step details based on the type
    if step.type == "message_creation":
        message_id = step.step_details.message_creation.message_id
        message_details = retrieve_message(client, step.thread_id, message_id)
        step_dict["steps"] = [
            {
                "type": c["type"],
                "content": c["text"]["value"] if c["type"] == "text" else c["image_file"]["file_id"]
            }
            for c in message_details["content"]
        ]
    elif step.type == "tool_calls":
        tool_calls = []
        for tool_call in step.step_details.tool_calls:
            if tool_call.type == "code_interpreter":
                tool_calls.append({
                    "type": "code",
                    "content": tool_call.code_interpreter.input
                })
                for output in tool_call.code_interpreter.outputs:
                    if output.type == "image":
                        tool_calls.append({
                            "type": "image",
                            "content": output.image.file_id
                        })
            step_dict["steps"] = tool_calls
    
    return step_dict
