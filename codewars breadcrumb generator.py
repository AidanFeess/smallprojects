def format(addon, position, active):
    position = position.upper()
    position = position.split('.')[0]
    position = position.split('?')[0]
    position = position.split('#')[0]

    slspos = position.lower()

    ignore = ["the", "of", "in", "from", "by", "with", "and", "or", "for", "to", "at", "a"]

    if len(position) > 30:
        position=position.split('-')
        x=''
        for n in position:
            if n.lower() not in ignore:
                x+=n[0]
        position=x
    else:
        position = ''.join(n+' ' for n in position.split('-'))[:-1]

    sls = f'/{slspos}/'
    if position == 'HOME':
        sls = '/'
    if active:
        return f'<span class="active">{position}</span>' 
    else:
        return f'<a href="{addon}{sls}">{position}</a>' 

def generate_bc(url, separator):
    url = url.split(':')
    if len(url) > 1:
        url.pop(0)
    url = ''.join(n for n in url)
    url = url.split('/')
    final = ''
    addon = ''
    while '' in url:
        for x in url:
            if x == '':
                url.remove(x)
    url[0] = 'HOME'
    

    for dir in range(len(url)):
        a = False
        try:
            if dir == len(url)-1 or 'index' in url[dir+1]: # we need to check if the next url is an index
                a = True
                if 'index' in url[dir]: return final # index directories get sent back to last directory
        except:
            pass

        final += format(addon, url[dir], a)
        final += f'{separator}' if a == False else ''

        if dir != len(url)-1 and dir > 0 and len(url) > 2:
            addon += f'/{url[dir]}'

    return final

print(generate_bc('https://archive.wrccdc.org/images/2020/', ' * '))