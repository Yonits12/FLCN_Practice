print(len('Yoni'))
exit()
word = '0123456789'
word = word[:3] + '__' + word[6:]
print(word)

try:
    int(word, 2)
    print("Binary!")
except Exception:
    print("Nor binary!")
exit()

dictio = {'Yoni': '123', 'Anna': '456'}
print(dictio['Anna'])
exit()

yoni1 = str('MOV+78')
print(yoni1.replace('MOV', '12'))


print("____") if 0 else print("^^^^^")

word = '1111010001110000'
print(word)
word = word[:7] + '11' + word[9:]
print(word)

words = [1,2,3,4,5,6]
print(words)
words[2:4] = [0,0,0]
print(words)

def func(line):
    word1 = line + '00000000'
    return word1


all_lines = ['123', '456', '789']

for index, line in enumerate(all_lines):
    all_lines[index] = func(line)
print(all_lines)

print(type(format(int('1'), '016b')))