import sqlite3

connection = sqlite3.connect('etd_back_020722_3PM.db')
cursor = connection.cursor()

""" Using fetchall results in retrieving multiple records for some ETDs. 
Currently using fetchone """

cursor.execute("select * from merritt_ingest where local_id like '%ucsd19786';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20150';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20266';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20348';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20349';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20409';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20426';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20435';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20451';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20476';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20484';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20491';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20500';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20509';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20527';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20530';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20536';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20557';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20571';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20572';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20583';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20584';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20587';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20589';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20592';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20593';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20595';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20596';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20600';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20606';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20607';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20608';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20609';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20615';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20627';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20630';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20631';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20635';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20637';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20638';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20640';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20646';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20647';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20653';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20655';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20656';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20658';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20660';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20666';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20667';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20668';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20669';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20673';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20674';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20679';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20680';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20681';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20688';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20695';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20696';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20698';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20703';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20705';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20706';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20715';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20719';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20720';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20723';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20724';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20726';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20732';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20735';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20742';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20746';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20749';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20750';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20755';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20757';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20763';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20767';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20769';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20773';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20775';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20777';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20782';")
print(cursor.fetchone())
cursor.execute("select * from merritt_ingest where local_id like '%ucsd20786';")
print(cursor.fetchone())

connection.close()

