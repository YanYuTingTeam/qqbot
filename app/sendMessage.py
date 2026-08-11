from botpy.message import GroupMessage
import os
import sys
from urllib.parse import quote
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension.image import *
from extension.audio import *

class sendMessage:
    async def text(content: str, message: GroupMessage, seq: int = 1):
        await message._api.post_group_message(
            group_openid=message.group_openid,
            msg_id=message.id,
            msg_type=2,
            markdown={"content": content.replace('\n','\u200b\n')},
            msg_seq=seq
        )

    async def texttrue(content: str, message: GroupMessage, seq: int = 1):
        await message._api.post_group_message(
            group_openid=message.group_openid,
            msg_id=message.id,
            #content=content.replace('.','/'),
            content=content,
            msg_seq=seq
        )

    def at(atid: str = None):
        if atid:
            return f'<qqbot-at-user id="{atid}" />'
        else:
            return ""

    async def markdown(content: str, message: GroupMessage, seq: int = 1):
        await message._api.post_group_message(
            group_openid=message.group_openid,
            msg_id=message.id,
            msg_type=2,
            markdown={"content": content},
            msg_seq=seq
        )

    async def buttonLink(content: str, url: str, message: GroupMessage, seq: int = 1):
        await message._api.post_group_message(
            group_openid=message.group_openid,
            msg_id=message.id,
            msg_type=2,
            markdown={"content": content},
            keyboard={
                "content": {
                    "rows": [
                        {
                            "buttons": [
                                {
                                    "id": "play_url",
                                    "render_data": {
                                        "label": "\u25b6\u70b9\u51fb\u64ad\u653e",
                                        "visited_label": "\u25b6\u5df2\u6253\u5f00",
                                        "style": 1
                                    },
                                    "action": {
                                        "type": 2,
                                        "permission": {"type": 2},
                                        "data": url
                                    }
                                }
                            ]
                        }
                    ]
                }
            },
            msg_seq=seq
        )

    async def image(url, message: GroupMessage, seq: int = 1):
        uploadMedia = await message._api.post_group_base64file(
                group_openid=message.group_openid, 
                file_type=1,
                file_data=image_to_base64(url)
            )
        await sendMessage.media(
            message=message,
            media=uploadMedia,
            msg_seq=seq
        )

    async def audio(url, message: GroupMessage, seq: int = 1):
        uploadMedia = await message._api.post_group_base64file(
                group_openid=message.group_openid, 
                file_type=3,
                file_data=audio_to_silk(url)
            )
        await sendMessage.media(
            message=message,
            media=uploadMedia,
            msg_seq=seq
        )

    async def audioT(url, message: GroupMessage, seq: int = 1):
        uploadMedia = await message._api.post_group_base64file(
                group_openid=message.group_openid, 
                file_type=3,
                file_data=url
            )
        await sendMessage.media(
            message=message,
            media=uploadMedia,
            msg_seq=seq
        )

    async def audioTest(url, message: GroupMessage, seq: int = 1):
        uploadMedia = await message._api.post_group_file(
                group_openid=message.group_openid, 
                file_type=3,
                url=url
            )
        await sendMessage.media(
            message=message,
            media=uploadMedia,
            msg_seq=seq
        )

    async def media(media, message: GroupMessage, msg_seq):
        await message._api.post_group_message(
            msg_id=message.id,
            group_openid=message.group_openid,
            msg_type=7,
            media=media,
            msg_seq=msg_seq
        )