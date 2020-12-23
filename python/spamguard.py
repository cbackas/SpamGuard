import os, re
from datetime import datetime
from mailsuite.imap import IMAPClient

# get current timestamp for prints
def current_time():
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

# checks raw email html for some spam patterns i've found
def check_for_spam(text_html):
    text_html = str(text_html)

    # oh yea? I won a ps5?
    if 'lucky online winner' in text_html.lower():
        return True

    # CONSTANTLY get emails with this HTML format
    evil_html_pattern = r'<metahttp-equiv="Content-Type"content="text\/html;charset=utf-8">\\r\\n(<divstyle="text-align:center;">\\r\\n<tablealign="center">|<divdir="ltr">\\r\\n<center>\\r\\n<table>)\\r\\n<tr>\\r\\n<td>\\r\\n<ahref=".+">\\r\\n\\t\\t<imgsrc=".+">\\r\\n\\t<\/a>\\r\\n<\/td>\\r\\n<\/tr>\\r\\n<tr>\\r\\n<tdstyle="padding-top:200px;">\\r\\n<ahref=".+">\\r\\n\\t\\t<imgsrc=".+">\\r\\n\\t<\/a>\\r\\n<\/td>'
    text_html = ''.join(text_html.split())
    match = re.findall(evil_html_pattern, text_html)
    if len(match) > 0:
        return True

    return False

# function thats called when IDLE tells us a email was recieved
def callback(obj: IMAPClient):
    unseen_msg_uids = obj.search(u'UNSEEN')
    spam_uids = []
    for msg_uid in unseen_msg_uids:
        message = obj.fetch_message(msg_uid, parse=True)
        is_spam = check_for_spam(message['text_html'])
        if is_spam:
            spam_uids.append(msg_uid)

    # when we fetched all the emails they were marked as read
    # so lets undo that by resetting all their flags
    obj.set_flags(unseen_msg_uids, ())

    # Send the spam to the executioner
    if len(spam_uids) > 0:
        print(f'[{current_time()}] Deleting Spam: {spam_uids}')
        obj.delete_messages(spam_uids)

if __name__ == "__main__":
    # Env vars needed
    imap_host = os.getenv('IMAP_HOST', '')
    imap_port = os.getenv('IMAP_PORT', '993')
    username = os.getenv('AUTH_USERNAME', '')
    password = os.getenv('AUTH_PASSWORD', '')

    if imap_host and username and password:
        print(f'[{current_time()}] Starting IMAP client in idle mode...')
        IMAPClient(host=imap_host, username=username, password=password, port=int(imap_port), idle_callback=callback)
    else:
        print(f'[{current_time()}] [ERROR] Environment variables not properly set. Make sure you\'ve set IMAP_HOST, AUTH_USERNAME, and AUTH_PASSWORD variables.')