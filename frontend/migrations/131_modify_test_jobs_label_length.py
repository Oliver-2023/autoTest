def migrate_up(mgr):
    mgr.execute("alter table tko_jobs modify column label varchar(255);")

def migrate_down(mgr):
    mgr.execute("alter table tko_jobs modify column label varchar(100);")
