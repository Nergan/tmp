from sys import argv

from asyncio import sleep

from pywebio import start_server
from pywebio.input import input, input_group, actions
from pywebio.output import output, put_scrollable, put_markdown
from pywebio.session import defer_call, info as session_info, run_async, run_js

chat_msgs = []
online_users = set()

async def main():
    global chat_msgs

    msg_box = output()
    put_scrollable(msg_box, height=290, keep_bottom=True)

    nickname = await input(required=True, placeholder="Username",
                           validate=lambda n: "This nickname is already in use" if n in online_users or n == '📢' else None)
    online_users.add(nickname)

    chat_msgs.append(('📢', f'`{nickname}` joined'))
    msg_box.append(put_markdown(f'📢 `{nickname}` joined'))

    refresh_task = run_async(refresh_msg(nickname, msg_box))

    while True:
        data = await input_group("💭 new message", [
            input(placeholder="message...", name="msg"),
            actions(name="cmd", buttons=["send", {'label': "Leave", 'type': 'cancel'}])
        ], validate = lambda m: ('msg', "Message") if m["cmd"] == "Send" and not m['msg'] else None)

        if data is None:
            break

        msg_box.append(put_markdown(f"`{nickname}`: {data['msg']}"))
        chat_msgs.append((nickname, data['msg']))

    refresh_task.close()

    online_users.remove(nickname)
    toast("Вы вышли из чата!")
    msg_box.append(put_markdown(f'📢 `{nickname}` leave'))
    chat_msgs.append(('📢', f'`{nickname}` leave'))

    put_buttons(['Reconnect'], onclick=lambda btn:run_js('window.location.reload()'))

async def refresh_msg(nickname, msg_box):
    global chat_msgs
    last_idx = len(chat_msgs)

    while True:
        await sleep(1)
        
        for m in chat_msgs[last_idx:]:
            if m[0] != nickname: # if not a message from current user
                msg_box.append(put_markdown(f"`{m[0]}`: {m[1]}"))
        
        # remove expired
        if len(chat_msgs) > MAX_MESSAGES_COUNT:
            chat_msgs = chat_msgs[len(chat_msgs) // 2:]
        
        last_idx = len(chat_msgs)

if __name__ == "__main__":   
   
    global PORT, MAX_MESSAGES_COUNT
    PORT, MAX_MESSAGES_COUNT = 8080, 100
    
    if len(argv) > 1:
        PORT = argv[1]
        
        if len(argv) > 2:
            MAX_MESSAGES_COUNT = argv[2]
    
    start_server(main, debug=True, port=PORT, cdn=False)