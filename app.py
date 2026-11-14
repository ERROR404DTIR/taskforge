#!/usr/bin/env python3
"""TaskForge — local Kanban CLI. Python 3.9+, no external packages."""
import argparse,datetime as dt,json,sqlite3,sys
from pathlib import Path
DB=Path(__file__).with_name("taskforge.db")
STATUSES=("todo","doing","done")
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
 c.execute("""CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY,title TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'todo',priority TEXT NOT NULL DEFAULT 'normal',due TEXT,board TEXT NOT NULL DEFAULT 'default',created TEXT NOT NULL)"""); return c
def main():
 p=argparse.ArgumentParser(description="A local Kanban board"); s=p.add_subparsers(dest="cmd",required=True)
 a=s.add_parser("add"); a.add_argument("title"); a.add_argument("--priority",choices=["low","normal","high"],default="normal"); a.add_argument("--due"); a.add_argument("--board",default="default")
 m=s.add_parser("move"); m.add_argument("id",type=int); m.add_argument("status",choices=STATUSES)
 l=s.add_parser("list"); l.add_argument("--board",default="default"); l.add_argument("--status",choices=STATUSES); l.add_argument("--all-boards",action="store_true")
 d=s.add_parser("delete"); d.add_argument("id",type=int)
 ex=s.add_parser("export"); ex.add_argument("file",nargs="?",default="taskforge.json")
 im=s.add_parser("import"); im.add_argument("file")
 args=p.parse_args(); c=db()
 if args.cmd=="add":
  if args.due:
   try: dt.date.fromisoformat(args.due)
   except ValueError: sys.exit("Due date must be YYYY-MM-DD")
  cur=c.execute("INSERT INTO tasks(title,priority,due,board,created) VALUES(?,?,?,?,?)",(args.title,args.priority,args.due,args.board,dt.datetime.now().isoformat(timespec="seconds"))); c.commit(); print("Created task #"+str(cur.lastrowid))
 elif args.cmd=="move":
  cur=c.execute("UPDATE tasks SET status=? WHERE id=?",(args.status,args.id)); c.commit(); print("Updated." if cur.rowcount else "Task not found.")
 elif args.cmd=="list":
  sql="SELECT * FROM tasks WHERE 1=1"; vals=[]
  if not args.all_boards: sql+=" AND board=?"; vals.append(args.board)
  if args.status: sql+=" AND status=?"; vals.append(args.status)
  rows=c.execute(sql+" ORDER BY CASE status WHEN 'doing' THEN 0 WHEN 'todo' THEN 1 ELSE 2 END, CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, due",vals)
  for status in STATUSES:
   print("\n"+status.upper())
   for x in rows:
    if x["status"]==status: print(f"  #{x['id']} [{x['priority']}] {x['title']}"+(f" — due {x['due']}" if x["due"] else "")+f"  ({x['board']})")
 elif args.cmd=="delete":
  cur=c.execute("DELETE FROM tasks WHERE id=?",(args.id,)); c.commit(); print("Deleted." if cur.rowcount else "Not found.")
 elif args.cmd=="export":
  rows=[dict(x) for x in c.execute("SELECT * FROM tasks ORDER BY id")]
  Path(args.file).write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding="utf-8"); print("Exported",len(rows),"tasks.")
 elif args.cmd=="import":
  data=json.loads(Path(args.file).read_text(encoding="utf-8")); count=0
  for x in data:
   if not x.get("title"): continue
   c.execute("INSERT INTO tasks(title,status,priority,due,board,created) VALUES(?,?,?,?,?,?)",(x["title"],x.get("status","todo") if x.get("status") in STATUSES else "todo",x.get("priority","normal") if x.get("priority") in ("low","normal","high") else "normal",x.get("due"),x.get("board","default"),x.get("created",dt.datetime.now().isoformat(timespec="seconds")))); count+=1
  c.commit(); print("Imported",count,"tasks.")
 c.close()
if __name__=="__main__": main()
