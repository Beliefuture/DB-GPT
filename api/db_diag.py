import logging
from flask import Blueprint, request
from datetime import datetime
from api.utils.code import ResponseCode
from api.utils.response import ResMsg
from api.utils.util import route
from multiagents.multiagents import MultiAgents
import pdb

multi_agents = MultiAgents.from_task("agent_conf")

bp = Blueprint("db_diag", __name__, url_prefix='/db_diag')

logger = logging.getLogger(__name__)

from utils.core import read_yaml, openai_completion_create, save_chat_history, get_chat_history


@route(bp, '/robot_intro', methods=["POST"])
def robot_intro():
    """
    return robot introduce
    :return:
    """
    res = ResMsg()

    prompts_conf = read_yaml('prompts', 'agentverse/tasks/db_diag/config.yaml')

    try:
        prompts = [prompts_conf.get('chief_dba_format_prompt'), prompts_conf.get('cpu_agent_format_prompt'), prompts_conf.get('mem_agent_format_prompt')]
        senders = ['Chief DBA', 'CPU Agent', 'Memory Agent']
        resluts = []
        for i in range(len(prompts)):
            prompt = prompts[i]
            sender = senders[i]
            format_prompt = f"分析后面的prompt，然后使用第一人称简单的介绍一下自己，控制在100个字以内，使用英文回复。：{prompt}"
            message = [
                {"role": "user", "content": format_prompt}
            ]
            openai_resp = openai_completion_create(message)
            content = openai_resp.get('choices', [])[0].get('message').get('content')
            result = {"content": content, "sender": sender, "type": "robot_intro", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            resluts.append(result)
        res.update(data=resluts)
        return res.data

    except Exception as error:
        logger.error(error)
        res.update(code=ResponseCode.Fail)
        return res.data


@route(bp, '/run', methods=["POST"])
def run():
    """
    return start gradio
    :return:
    """
    res = ResMsg()
    obj = request.get_json(force=True)
    analyse_at = obj.get("analyse_at")
    start_at = obj.get("start_at")
    end_at = obj.get("end_at")

    # 未获取到参数或参数不存在
    if not obj or not start_at or not start_at or not analyse_at:
        res.update(code=ResponseCode.InvalidParameter)
        return res.data
    # 将start_at和end_at写入文件
    with open("./diag_time.txt", "a") as f:
        f.write(str(start_at) + "-" + str(end_at) + "\n")
    multi_agents.reset()
    results = multi_agents.next()
    result = {}
    # 判断是否是数组，如果是数组，且长度大于1，取第一个值
    if isinstance(results, list) and len(results) > 0:
        result = results[0]
        result = {"content": result.content, "sender": result.sender, "type": "message", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        save_chat_history(result, analyse_at)
    res.update(data=result)
    return res.data


@route(bp, '/next_step', methods=["POST"])
def next_step():
    """
    return start gradio
    :return:
    """
    res = ResMsg()
    obj = request.get_json(force=True)
    analyse_at = obj.get("analyse_at")
    # 未获取到参数或参数不存在
    if not obj or not analyse_at:
        res.update(code=ResponseCode.InvalidParameter)
        return res.data
    results = multi_agents.next()
    result = {}
    # 判断是否是数组，如果是数组，且长度大于1，取第一个值
    if isinstance(results, list) and len(results) > 0:
        result = results[0]
        result = {"content": result.content, "sender": result.sender, "type": "message", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        save_chat_history(result, analyse_at)
    res.update(data=result)
    return res.data


@route(bp, '/submit', methods=["POST"])
def submit():
    """
    return start gradio
    :return:
    """
    res = ResMsg()
    obj = request.get_json(force=True)
    message = obj.get("message")
    results = multi_agents.submit(message)
    result = None
    # 判断是否是数组，如果是数组，且长度大于1，取第一个值
    if isinstance(results, list) and len(results) > 0:
        result = results[0]
        result = {"content": result.content, "sender": result.sender, "type": "message", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    res.update(data=result)
    return res.data


@route(bp, '/chat_history', methods=["POST"])
def chat_history():
    """
    return chat_history
    :return:
    """
    res = ResMsg()
    res.update(data=get_chat_history())
    return res.data


@route(bp, '/reset', methods=["POST"])
def reset():
    """
    return start gradio
    :return:
    """
    res = ResMsg()
    multi_agents.reset()
    res.update(data={})
    return res.data

