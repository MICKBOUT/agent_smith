def upper_ctr(letters):
    count = 0
    for char in letters:
        if char.isupper():
            count += 1
    return count

assert upper_ctr('PYthon') == 1
assert upper_ctr('BigData') == 1
assert upper_ctr('program') == 0



def upper_ctr(str):
    upper_ctr = 0
    for i in range(len(str)):
        if str[i] >= 'A' and str[i] <= 'Z':
            upper_ctr += 1
        return upper_ctr
