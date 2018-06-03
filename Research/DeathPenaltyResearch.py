'''
The following code crawls through the website of the Texas Department of Criminal Justice
& gathers the contents of the paragraphs in the 'Last Statement' links

'''
#Import  classes
from bs4 import BeautifulSoup
import urllib.request, urllib.parse, urllib.error
import ssl, sqlite3, re

'''
By passing SSL certificate requirements of python
'''
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

'''
Creating an sqlite database called 'wordFile.sqlite' to store the words along with their
frequency count
'''
conn = sqlite3.connect('wordFile.sqlite')
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS WORD_FILE
                (WORD TEXT UNIQUE, AMOUNT INTEGER)''')

'''
converting website to string, storing in a variable, sending it as a parameter,
and reading the returned content, storing in 'html' variable, sending that as
parameter to BeautifulSoup class
'''
url = 'http://www.tdcj.state.tx.us/death_row/dr_executed_offenders.html'
html = urllib.request.urlopen(url, context=ctx).read()
soup = BeautifulSoup(html, 'html.parser')

'''
Creating a list called 'texts' to store suffix to be added onto the url string
'''
texts = list()

'''
Find all the 'tr' tags and loop through starting from the index 1. Index 0 contains
schema for the rest of the table
'''
for tags in soup.find_all('tr')[1:]:
    column = tags.find_all('td')
    anchorLine = column[2].find('a') #column now contains 2 data points each with its own anchor tags
    #access the 2nd data point and extract
    texts.append(anchorLine.get('href', None))

# Create a dictionary called wordsDictionary
wordsDictionary = dict()

'''
Loop through 'texts' list that contains the suffix for the link containing the offenders last staements
'''
countOfNoLastStatement = 0 #Declare and initialize variable to count number of offenders with no last statements
for site in texts:
    if re.search(('no_last_statement'), site):
        countOfNoLastStatement += 1
        continue
    '''
    Some suffix in the shortened sites contain unexpected prefixes. The following lines get rid of 2 prefixes: a string
    and a character, respectively
    '''
    if site.startswith('/death_row/'): site = site[10:]
    if site.startswith('/'): site = site[1:]

    site = 'http://www.tdcj.state.tx.us/death_row/' + site
    site = str(site)

    try:
        html1 = urllib.request.urlopen(site, context=ctx).read()
        soup1 = BeautifulSoup(html1, 'html.parser')
        paragraphTag = soup1('p') # p is for paragraph tags
        sentence = paragraphTag[5].text
        wordsInSentence = sentence.split() #split the sentence into words and return a list

        for word in wordsInSentence: #loop through the list of word
            word = word.strip()
            '''
            If the word is less than 4 characters, skip it. If it has a period, colon, comma at the end
            remove those characters
            '''
            if len(word) < 4: continue

            if word.endswith('.') or word.endswith(':') or word.endswith(','): word = word[:-1]

            '''
            Statistically, nouns have more than 1 vowel
            The following few lines of code skips the words with less than
            2 vowels
            '''
            count = 0
            for character in word:
                if character in ['a','e','i','o','u']:
                    count += 1
            if count < 2: continue

            '''
            The following code checks to see if the word is a contraction
            Contraction words are not useful for the context of this project
            '''
            apostrophe = False
            for character in word:
                if character == "'": apostrophe = True
            if apostrophe == True: continue

            #Add the word into a dictionary called 'wordsDictionary', along with a count of its frequency

            word = word.upper()
            wordsDictionary[word] = wordsDictionary.get(word,0) + 1
        #print('Passed...')

    except:
        print('Failed. Site is: ', site)
        continue
print(countOfNoLastStatement, 'offenders did not make any last statements')

print('Adding into sqlite file...')

'''
The following code itemizes the pairs in the dictionary and loops through each of the pair
**(Optional)** It will skip the pair that has a frequency count of less than 20
The remaining pairs will be inserted into an sqlite file called 'wordFile.sqlite' for easier
graphing purposes
'''

for key, value in wordsDictionary.items():
    #if value < 20: continue
    cur.execute('''INSERT OR IGNORE INTO WORD_FILE VALUES (?,?)''',(key, value))
cur.execute('''SELECT * FROM WORD_FILE ORDER BY AMOUNT DESC''')
conn.commit()
cur.close()
