import os, re, time
from socket import gaierror
from datetime import datetime
from mailsuite.imap import IMAPClient
import imapclient.exceptions
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
        r'<html><head>\\r\\n<metahttp-equiv=\"Content-Type\"content=\"text/html;charset=iso-8859-1\">\\r\\n<styletype=\"text/css\"style=\"display:none;\">P{margin-top:0;margin-bottom:0;}</style>\\r\\n</head>\\r\\n<bodydir=\"ltr\">\\r\\n<center>\\r\\n<ahref=\".+\">\\r\\n<imgsrc=\".+\">\\r\\n</a>\\r\\n<divstyle=\"padding-top:200px;\">\\r\\n',
        r'<center>\\r\\n<div>\\r\\n<ahref=\".+\"><imgsrc=\".+\"/></a>\\r\\n<br/><br/>\\r\\n<ahref=\".+\"><imgsrc=\".+\"/></a>\\r\\n</div>',
        r'<divstyle="text-align:center">\\r\\n<ahref=".+"><imgsrc=".+"/></a>\\r\\n<divstyle=\"padding-top:[0-9]+px;\"><ahref=\".+\"><imgsrc=\".+\"/></a></div>',
        r'<divstyle="text-align:center">\\r\\n<ahref=".+"><imgsrc=".+"/></a></div>\\r\\n<divstyle="text-align:center;padding-top:200px;"><ahref=".+"><imgsrc=".+"/></a></p>\\r\\n</div>',
        r'<divstyle="text-align:center">\\r\\n<ahref=".+">.+<imgsrc=".+"/></a>\\r\\n\\r\\n<divstyle="padding-top:[0-9]+px;"><ahref=\".+\"><imgsrc=\".+\"/></a></div>',
        r'<divstyle="text-align:center">\\r\\n<ahref=".+">\\r\\n<imgsrc=".+"/></a>\\r\\n<divstyle="padding-top:200px;"><ahref=".+">\\r\\n<imgsrc=".+"/></a></div>\\r\\n</div>\\r\\n<imgsrc=".+"/>',
        r'<!DOCTYPEhtmlPUBLIC\"-//W3C//DTDXHTML1.0Transitional//EN\"\"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\"><htmlxmlns=\"http://www.w3.org/1999/xhtml\"><head>\\r\\n<metahttp-equiv=\"Content-Type\"content=\"text/html;charset=utf-8\"><body>\\r\\n<center><ahref=\".+\">',
        r'<pstyle="text-align:center">\\r\\n<ahref=".+"><imgsrc=".+"/></a></p>\\r\\n<divstyle="text-align:center;padding-top:[0-9]+px;"><ahref=".+"><imgsrc=".+"/></a></p>\\r\\n</div>',
        r'<!doctypehtml><metahttp-equiv="Content-Type"content="text/html;charset=us-ascii"><center><divalign="center">\\r\\n<h1><ahref=".+"style="text-decoration:none;color:#ef680f;ElevenElefont-weight:bold;font-size:1\.2em;"><span>.+</span></a></h1>\\r\\n<center><ahref=".+"><imgsrc=".+"></a></div>',
        r'<tablerole="presentation"class="wrapfull-wrap"width="100%"border="0"cellspacing="0"cellpadding="0"align="center"bgcolor="#f5f5f5"style="background-color:#f5f5f5;margin-top:10px;">\\r\\n<tr>\\r\\n<tdalign="center"><tablerole="presentation"border="0"cellspacing="0"cellpadding="0"class="wrap"width="700"align="center"bgcolor="#FFFFFF"style="background-color:#FFFFFF;">\\r\\n<tr>\\r\\n<tdalign="center"bgcolor="#f5f5f5"style="background-color:#f5f5f5;">\\r\\n\\r\\n<!--startmessagecontent-->\\r\\n<tableclass="wrap"width="700"border="0"cellspacing="0"cellpadding="0"align="center"bgcolor="#f5f5f5"style="background-color:#f5f5f5;">\\r\\n<tr>\\r\\n<tdstyle="padding:5px0px0px;"align="center"><tablealign="center"class="wrap"width="700"border="0"cellspacing="0"cellpadding="0">\\r\\n<tr>\\r\\n<tdwidth="295"class="preheader-linkcenter"style="font-size:12px;"><adata-link-name="PREHEADER-HallmarkwillairbrandnewmovieseverySaturdayinJanuary!"',
        r'<!DOCTYPEhtml><html><head>\\r\\n<metahttp-equiv="Content-Type"content="text\/html;charset=utf-8"><metaname="format-detection"content="telephone=no">\\r\\n<metaname="viewport"content="width=device-width,initial-scale=1\.0;user-scalable=no;">\\r\\n<metahttp-equiv="X-UA-Compatible"content="IE=9;IE=8;IE=7;IE=EDGE">\\r\\n<style>\\r\\nbody{width:100%!important;height:100%!important;margin:0;padding:0;}\\r\\ntable,tabletd{border-collapse:collapse!important;}\\r\\ntableth{margin:0!important;padding:0!important;font-weight:normal;}\\r\\n\\r\\nbody,table,td,a{-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;}\\r\\nReadMsgBody{width:100%;}\.ExternalClass{width:100%;}\\r\\nExternalClass{width:100%;}\\r\\nExternalClass,\.ExternalClassp,\.ExternalClassspan,\.ExternalClassfont,\.ExternalClasstd,\.ExternalClassdiv{line-height:100%;}\\r\\nh4{\\r\\n\\tfont-size:14px;\\r\\n\\tmargin:0;\\r\\n\\tfont-weight:normal;\\r\\n\\tdisplay:none;\\r\\n}\\r\\n\\r\\ntable{\\r\\ntext-align:left;\\r\\n}\\r\\n\\r\\ntd{\\r\\nfont-family:Arial,sans-serif;\\r\\n}\\r\\n\\r\\nappleBodya{color:#68440a;text-decoration:none;}\\r\\nappleFootera{color:#999999;text-decoration:none;}\\r\\n\\r\\nemailBody{\\r\\nwidth:375px;\\r\\nbackground-color:#fafafa;\\r\\n}\\r\\n\\r\\nemailBodyTD{\\r\\npadding-left:17px;\\r\\npadding-right:18px;\\r\\npadding-top:23px;\\r\\npadding-bottom:21px;\\r\\n}\\r\\n\\r\\nbrandTable{\\r\\nmargin-bottom:20px;\\r\\nwidth:100%;\\r\\nmin-width:338px;\\r\\n}\\r\\n\\r\\nbrandImage{\\r\\nwidth:130px;\\r\\n}\\r\\n\\r\\nemailContainer{\\r\\nbackground-color:#ffffff;\\r\\nborder-left:1pxsolid#D6D6D6;\\r\\nborder-right:1pxsolid#D6D6D6;\\r\\nborder-bottom:1pxsolid#D6D6D6;\\r\\nborder-top:2pxsolid#CECECE;\\r\\n}\\r\\n\\r\\nemailContainerTD{\\r\\npadding-left:23px;\\r\\npadding-right:23px;\\r\\npadding-top:25px;\\r\\npadding-bottom:33px;\\r\\n}\\r\\n\\r\\ngreetingTable{\\r\\nfont-size:20px;\\r\\nline-height:24px;\\r\\ncolor:#002E36;\\r\\nmargin-bottom:18px;\\r\\n}\\r\\n\\r\\ninformationTable{\\r\\nfont-size:18px;\\r\\nline-height:24px;\\r\\ncolor:#002E36;\\r\\n}\\r\\n\\r\\ninformationTabletd{\\r\\npadding-bottom:18px;\\r\\n}\\r\\n\\r\\ninformationTablea{\\r\\ncolor:#002E36;\\r\\ntext-decoration:none;\\r\\n}\\r\\n\\r\\ntextWithUnderlinedLink{\\r\\ncolor:#002E36;\\r\\ntext-decoration:none;\\r\\nborder-bottom:2pxsolid#00DFFC;\\r\\n}\\r\\n\\r\\nmsoInformationTable{\\r\\nfont-size:18px;\\r\\nline-height:24px;\\r\\ncolor:#002E36;\\r\\n}\\r\\n\\r\\nmsoInformationTabletd{\\r\\npadding-bottom:18px;\\r\\n}\\r\\n\\r\\nmsoInformationTablea{\\r\\ncolor:#002E36;\\r\\ntext-decoration:underline;\\r\\ntext-decoration-color:#00DFFC;\\r\\n}\\r\\n\\r\\norderDetailsTable{\\r\\nfont-size:15px;\\r\\nline-height:20px;\\r\\n}\\r\\n\\r\\norderDetailsTableLink{\\r\\ntext-decoration:none;\\r\\ncolor:#008296;\\r\\n}'
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
        # loop keeps IMAPClient alive even after it dies
        while True:
            try:
                # start IMAP client (blocking)
                print(f'[{current_time()}] Starting IMAP client in idle mode...')
                IMAPClient(host=imap_host, username=username, password=password, port=int(imap_port), idle_callback=callback)
            except imapclient.exceptions.IMAPClientError:
                # auth failed so don't keep trying again
                print(f'[{current_time()}] Auth Failed: check username or password... Exiting.')
                break
            except gaierror:
                # host failed to resolve so don't try again
                # todo? allow retries but further apart so script doesn't totally die just cuz internet went out briefly?
                print(f'[{current_time()}] Error resolving IMAP_HOST... Exiting.')
                break
            except:
                # if something happens with IMAPclient then... just restart it i guess
                # todo? add restart counter that notifies me if it fails too often? seems like rare issue tho
                print(f'[{current_time()}] An Error occurred... restarting IMAPClient')
                time.sleep(10)
                continue
    else:
        print(f'[{current_time()}] [ERROR] Environment variables not properly set. Make sure you\'ve set IMAP_HOST, AUTH_USERNAME, and AUTH_PASSWORD variables.')