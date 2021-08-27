import os, re
from datetime import datetime
from mailsuite.imap import IMAPClient
from dotenv import load_dotenv

# switch dev mode from False to True to:
# read env vars from env file
# disable email deletion
# enable printing html of unmatched emails
dev_mode = False

# get current timestamp for prints
def current_time():
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

# checks raw email html for some spam patterns i've found
def check_for_spam(text_html):
    text_html = str(text_html)

    # oh yea? I won a ps5?
    if 'lucky online winner' in text_html.lower():
        return True

    # strip spaces from html text
    text_html = ''.join(text_html.split())

    # html regex patterns
    # was going to store these in externally configurable json but figured I need to open dev environment to create these patterns anyway so might as well keep them here
    # --- 
    # Need to add a new pattern but forgot how you did it in the first place!?
    # Step 1. Set dev_mode to True
    # Step 2. Take the output of the text_html for the offending email over to regex tester and get things matching
    # Step 3. Make things are escaped right!
    # Step 4. Add pattern to pattern list
    # Step 5. Set dev_mode to False and PUSH
    patterns = [
        r'<metahttp-equiv="Content-Type"content="text\/html;charset=utf-8">\\r\\n(<divstyle="text-align:center;">\\r\\n<tablealign="center">',
        r'<divdir="ltr">\\r\\n<center>\\r\\n<table>)\\r\\n<tr>\\r\\n<td>\\r\\n<ahref=".+">\\r\\n\\t\\t<imgsrc=".+">\\r\\n\\t<\/a>\\r\\n<\/td>\\r\\n<\/tr>\\r\\n<tr>\\r\\n<tdstyle="padding-top:200px;">\\r\\n<ahref=".+">\\r\\n\\t\\t<imgsrc=".+">\\r\\n\\t<\/a>\\r\\n<\/td>',
        r'<divstyle=\"text-align:center\">\\r\\n<ahref=\".+\"><imgsrc=\".+\"/></a>\\r\\n<divstyle=\"padding-top:200px;\"><ahref=\".+\"><imgsrc=\".+\"/></a></div>',
        r'<html><head>\\r\\n<metahttp-equiv=\"Content-Type\"content=\"text/html;charset=iso-8859-1\">\\r\\n<styletype=\"text/css\"style=\"display:none;\">P{margin-top:0;margin-bottom:0;}</style>\\r\\n</head>\\r\\n<bodydir=\"ltr\">\\r\\n<center>\\r\\n<ahref=\".+\">\\r\\n<imgsrc=\".+\">\\r\\n</a>\\r\\n<divstyle=\"padding-top:200px;\">\\r\\n',
        r'<center>\\r\\n<div>\\r\\n<ahref=\".+\"><imgsrc=\".+\"/></a>\\r\\n<br/><br/>\\r\\n<ahref=\".+\"><imgsrc=\".+\"/></a>\\r\\n</div>',
        r'<divstyle="text-align:center">\\r\\n<ahref=\".+\">.+<imgsrc=\".+\"/></a>\\r\\n\\r\\n<divstyle="padding-top:200px;"><ahref=\".+\"><imgsrc=\".+\"/></a></div>',
        r'<!DOCTYPEhtmlPUBLIC\"-//W3C//DTDXHTML1.0Transitional//EN\"\"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\"><htmlxmlns=\"http://www.w3.org/1999/xhtml\"><head>\\r\\n<metahttp-equiv=\"Content-Type\"content=\"text/html;charset=utf-8\"><body>\\r\\n<center><ahref=\".+\">'
    ]
    # combine the patterns to go into 1 regex search
    combined_regex = "(" + ")|(".join(patterns) + ")"

    # return true if any of the patterns match
    match = re.findall(combined_regex, text_html)
    if len(match) > 0:
        if dev_mode:
            # helps to know an individual match happened sometimes
            print("match")
        
        return True
    
    if dev_mode:
        # print unmatched email's html
        print(text_html)

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
    if len(spam_uids) > 0 and not dev_mode:
        print(f'[{current_time()}] Deleting Spam: {spam_uids}')
        obj.delete_messages(spam_uids)


if __name__ == "__main__":
    if dev_mode:
        # load environment variables from .env file
        load_dotenv()

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