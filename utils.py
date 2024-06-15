def serialize_content(content):
    if content.type == "text":
        return {
            "type": content.type,
            "text": {
                "value": content.text.value,
                "annotations": content.text.annotations
            }
        }
    elif content.type == "image_file":
        return {
            "type": content.type,
            "image_file": {
                "file_id": content.image_file.file_id,
                "detail": content.image_file.detail
            }
        }
    elif content.type == "image_url":
        return {
            "type": content.type,
            "image_url": {
                "url": content.image_url.url,
                "detail": content.image_url.detail
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
            "object": message.object,
            "created_at": message.created_at,
            "thread_id": message.thread_id,
            "status": message.status,
            "incomplete_details": message.incomplete_details,
            "completed_at": message.completed_at,
            "incomplete_at": message.incomplete_at,
            "role": message.role,
            "content": [serialize_content(c) for c in message.content],
            "assistant_id": message.assistant_id,
            "run_id": message.run_id,
            "attachments": message.attachments,
            "metadata": message.metadata
        }
    except Exception as e:
        return {"error": str(e)}

def serialize_run_step(client, step):
    step_dict = {
        "id": step.id,
        "object": step.object,
        "created_at": step.created_at,
        "run_id": step.run_id,
        "assistant_id": step.assistant_id,
        "thread_id": step.thread_id,
        "type": step.type,
        "status": step.status,
        "cancelled_at": step.cancelled_at,
        "completed_at": step.completed_at,
        "expired_at": step.expired_at,
        "failed_at": step.failed_at,
        "last_error": None if step.last_error is None else {
            "code": step.last_error.code,
            "message": step.last_error.message,
            "expired_at": step.last_error.expired_at,
            "cancelled_at": step.last_error.cancelled_at,
            "failed_at": step.last_error.failed_at
        },
        "metadata": step.metadata,
        "usage": None if step.usage is None else {
            "prompt_tokens": step.usage.prompt_tokens,
            "completion_tokens": step.usage.completion_tokens,
            "total_tokens": step.usage.total_tokens
        }
    }
    
    # Add step details based on the type
    if step.type == "message_creation":
        message_id = step.step_details.message_creation.message_id
        message_details = retrieve_message(client, step.thread_id, message_id)
        step_dict["step_details"] = {
            "type": step.step_details.type,
            "message_creation": message_details
    }
    elif step.type == "tool_calls":
        tool_calls = []
        for tool_call in step.step_details.tool_calls:
            tool_call_dict = {
                "id": tool_call.id,
                "type": tool_call.type
            }
            if tool_call.type == "code_interpreter":
                tool_call_dict["code_interpreter"] = {
                    "input": tool_call.code_interpreter.input,
                    "outputs": [
                        {"type": output.type, "logs": output.logs} if output.type == "logs" else
                        {"type": output.type, "file_id": output.image.file_id}
                        for output in tool_call.code_interpreter.outputs
                    ]
                }
            elif tool_call.type == "file_search":
                tool_call_dict["file_search"] = {}
            elif tool_call.type == "function":
                tool_call_dict["function"] = {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                    "output": tool_call.function.output,
                    "last_error": None if tool_call.function.last_error is None else {
                        "code": tool_call.function.last_error.code,
                        "message": tool_call.function.last_error.message
                    }
                }
            tool_calls.append(tool_call_dict)
        step_dict["step_details"] = {
            "type": step.step_details.type,
            "tool_calls": tool_calls
        }
    
    return step_dict
