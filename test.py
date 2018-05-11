from run import JSONDocument

def test_json():
    document = JSONDocument('data/manual_australian_2018.json')
    print(document.find_page('fuel'))

if __name__ == '__main__':
    test_json()
