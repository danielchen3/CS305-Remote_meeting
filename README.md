# CS305-Remote_meeting
This is the project of CS305 Computer Network in SUSTech

1. `conf_client.py`中用户请求的格式应如下
{"type": "create"},  {"type": "join", "conferece_id": INT},  {"type": "quit"},  {"type": "cancel"},  //{"type": "switch", "conference_id": INT},  {"type": "view"} // 请求看会议名单,  {"type": "exit"}

2. 取消会议的逻辑是，如果是创建者只需要输入quit或者cancel，那么会议可以直接取消并且断开所有连接，如果不是创建者而是普通在会议中的人输入cancel会失败，他只能quit。

3. **在第一次连接时候会让用户进行一个认证，相当于是一个注册登录的过程**

4. Mainserver的response: {"status": True/False, "message": "string"} or {"status": True/False, "error": "string"}


**view**在多个会议的时候会有问题