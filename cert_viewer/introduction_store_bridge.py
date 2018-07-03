class IntroStore(object):
    def __init__(self, intro_db):
        self.intro_db = intro_db        

    def insert(self, intro):    	    	
        self.intro_db.introductions.insert_one(intro)
        print(intro)
        j=str(intro['_id'])
        #j=j[10:-2]
        intro['_id']=j
        print(intro)
        o=[]
        for x in intro:
        	o.append(intro[x])
        from . import app
        fileName=app.config['THEME']
        fileName='rosters\\'+fileName+'.csv'
        import csv
        csv.register_dialect('myDialect',quoting=csv.QUOTE_ALL,skipinitialspace=True)
        with open(fileName, 'a') as f:
        	writer = csv.writer(f, dialect='myDialect')
        	writer.writerow(o)
        f.close()
    



def insert_introduction(introduction):
    from cert_viewer import intro_store
    print("store")
    intro_store.insert(introduction)