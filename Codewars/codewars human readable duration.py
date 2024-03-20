def x(text, result, time, var, pos):
    text = time if var<2 else time + 's'
    if pos==0:
        result = f'{var} {text}'
    elif pos==1:
        result = f'{var} {text} and '+result 
    elif pos>1:
        result = f'{var} {text}, '+result
    pos+=1

    return text, result, pos

def format_duration(seconds):
    if seconds == 0:
        return 'now'
    minutes = int(seconds/60)
    hours = int(minutes/60)
    days = int(hours/24)
    years = int(days/365)
    seconds %= 60
    minutes-=hours*60
    hours-=days*24
    days-=years*365
    result = ''
    pos = 0
    text = ''

    if seconds:
        text = 'second' if seconds<2 else 'seconds'
        result = f'{seconds} {text}'
        pos+=1
    if minutes:  
        text = 'minute' if minutes<2 else 'minutes'
        result = f'{minutes} {text} and '+result if pos==1 else f'{minutes} {text}'
        pos+=1
    if hours:
        text, result, pos = x(text, result, 'hour', hours, pos)
    if days:
        text, result, pos = x(text, result, 'day', days, pos)
    if years:
        text, result, pos = x(text, result, 'year', years, pos)

    return result