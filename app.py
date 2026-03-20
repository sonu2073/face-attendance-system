"""
app.py  —  Face Attendance Desktop App
Run:  python app.py
"""
import os, sys, threading, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime

import cv2
from PIL import Image, ImageTk
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

sys.path.insert(0, os.path.dirname(__file__))
from database import db
from modules.face_engine import FaceEngine
from modules.exporter import export_daily, export_range
from modules.emailer import send_daily_report, schedule_daily

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

BG="  #0D1117"; BG2="#161B22"; BG3="#21262D"
GREEN="#00FF88"; GREEN2="#238636"; DIMGREEN="#2EA043"
RED="#F85149"; AMBER="#E3B341"; BLUE="#58A6FF"
TEXT="#E6EDF3"; MUTED="#8B949E"
FONT=("Courier New",11); FONT_SM=("Courier New",10)
FONT_LG=("Courier New",13,"bold"); FONT_XL=("Courier New",20,"bold")

BG = BG.strip()

# ─── LOGIN ───────────────────────────────────────────────────────────────────

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        db.init_db()
        self.title("Face Attendance — Login")
        self.geometry("420x520"); self.resizable(False,False)
        self.configure(fg_color=BG); self._build()
        self.eval("tk::PlaceWindow . center")

    def _build(self):
        ctk.CTkLabel(self,text="◉",font=("Courier New",48),text_color=GREEN).pack(pady=(48,0))
        ctk.CTkLabel(self,text="FACE_ATTEND",font=("Courier New",22,"bold"),text_color=GREEN).pack()
        ctk.CTkLabel(self,text="AI Attendance Management System",font=FONT_SM,text_color=MUTED).pack(pady=(2,36))
        f=ctk.CTkFrame(self,fg_color=BG2,corner_radius=10,border_width=1,border_color="#30363D")
        f.pack(padx=40,fill="x")
        ctk.CTkLabel(f,text="USERNAME",font=FONT_SM,text_color=MUTED).pack(anchor="w",padx=20,pady=(20,2))
        self.ue=ctk.CTkEntry(f,placeholder_text="admin",font=FONT,fg_color=BG3,border_color="#30363D",height=40)
        self.ue.pack(padx=20,fill="x")
        ctk.CTkLabel(f,text="PASSWORD",font=FONT_SM,text_color=MUTED).pack(anchor="w",padx=20,pady=(14,2))
        self.pe=ctk.CTkEntry(f,placeholder_text="••••••••",show="•",font=FONT,fg_color=BG3,border_color="#30363D",height=40)
        self.pe.pack(padx=20,fill="x"); self.pe.bind("<Return>",lambda e:self._login())
        self.el=ctk.CTkLabel(f,text="",text_color=RED,font=FONT_SM); self.el.pack(pady=(6,0))
        ctk.CTkButton(f,text="→  LOGIN",font=FONT_LG,fg_color=GREEN2,hover_color=DIMGREEN,height=44,command=self._login).pack(padx=20,pady=16,fill="x")
        ctk.CTkLabel(self,text="Default: admin / admin123",font=FONT_SM,text_color="#444").pack(pady=12)

    def _login(self):
        if db.verify_admin(self.ue.get().strip(), self.pe.get().strip()):
            u=self.ue.get().strip(); self.destroy(); MainApp(u).mainloop()
        else:
            self.el.configure(text="✗  Invalid credentials")


# ─── MAIN APP ────────────────────────────────────────────────────────────────

class MainApp(ctk.CTk):
    def __init__(self, username="admin"):
        super().__init__()
        self.username=username; self.engine=FaceEngine()
        self.title("Face Attendance System"); self.geometry("1280x780")
        self.minsize(1100,680); self.configure(fg_color=BG)
        self._build_layout(); self._show_page("camera")
        schedule_daily(self); self.protocol("WM_DELETE_WINDOW",self._on_close)

    def _build_layout(self):
        self.sidebar=ctk.CTkFrame(self,width=200,fg_color=BG2,corner_radius=0)
        self.sidebar.pack(side="left",fill="y"); self.sidebar.pack_propagate(False)
        ctk.CTkLabel(self.sidebar,text="FACE_ATTEND",font=("Courier New",13,"bold"),text_color=GREEN).pack(pady=(24,2))
        ctk.CTkLabel(self.sidebar,text=f"● {self.username}",font=FONT_SM,text_color=MUTED).pack(pady=(0,20))
        self.nav_buttons={}
        for key,label in [("camera","◉  Camera"),("students","≡  Students"),("dashboard","▦  Dashboard"),("export","⬇  Export"),("settings","⚙  Settings")]:
            btn=ctk.CTkButton(self.sidebar,text=label,anchor="w",font=FONT,height=42,fg_color="transparent",hover_color=BG3,text_color=MUTED,corner_radius=6,command=lambda k=key:self._show_page(k))
            btn.pack(padx=10,pady=2,fill="x"); self.nav_buttons[key]=btn
        ctk.CTkButton(self.sidebar,text="⏻  Logout",anchor="w",font=FONT_SM,height=36,fg_color="transparent",hover_color="#3D1A1A",text_color="#666",corner_radius=6,command=self._logout).pack(padx=10,pady=8,fill="x",side="bottom")
        self.content=ctk.CTkFrame(self,fg_color=BG,corner_radius=0); self.content.pack(side="left",fill="both",expand=True)

    def _show_page(self, key):
        for k,btn in self.nav_buttons.items():
            btn.configure(text_color=GREEN if k==key else MUTED, fg_color=BG3 if k==key else "transparent")
        for w in self.content.winfo_children():
            w.destroy()
        CameraPage._stop_flag=True
        pages={"camera":CameraPage,"students":StudentsPage,"dashboard":DashboardPage,"export":ExportPage,"settings":SettingsPage}
        kwargs={"camera":{"engine":self.engine},"students":{"engine":self.engine}}.get(key,{})
        if key=="settings": kwargs={"username":self.username}
        pages[key](self.content,**kwargs).pack(fill="both",expand=True)

    def _logout(self):
        CameraPage._stop_flag=True; self.destroy(); LoginWindow().mainloop()
    def _on_close(self):
        CameraPage._stop_flag=True; self.destroy()


# ─── CAMERA PAGE ─────────────────────────────────────────────────────────────

class CameraPage(ctk.CTkFrame):
    _stop_flag=False
    def __init__(self,parent,engine):
        super().__init__(parent,fg_color=BG)
        CameraPage._stop_flag=False; self.engine=engine
        self.running=False; self.current_match=None; self._build()

    def _build(self):
        hdr=ctk.CTkFrame(self,fg_color=BG2,height=52,corner_radius=0); hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr,text="LIVE CAMERA  /  ATTENDANCE",font=FONT_LG,text_color=GREEN).pack(side="left",padx=20)
        self.st_lbl=ctk.CTkLabel(hdr,text="● OFFLINE",font=FONT_SM,text_color=MUTED); self.st_lbl.pack(side="right",padx=20)
        body=ctk.CTkFrame(self,fg_color=BG); body.pack(fill="both",expand=True,padx=16,pady=16)
        left=ctk.CTkFrame(body,fg_color=BG); left.pack(side="left",fill="both",expand=True)
        self.vid=ctk.CTkLabel(left,text="",fg_color="#000",width=640,height=480); self.vid.pack()
        self.det=ctk.CTkLabel(left,text="[ NO SIGNAL ]",font=FONT,text_color=MUTED); self.det.pack(pady=8)
        br=ctk.CTkFrame(left,fg_color=BG); br.pack()
        self.cam_btn=ctk.CTkButton(br,text="▶  Start Camera",font=FONT,width=160,height=38,fg_color=GREEN2,hover_color=DIMGREEN,command=self._toggle)
        self.cam_btn.pack(side="left",padx=6)
        self.mk_btn=ctk.CTkButton(br,text="✓  Mark Attendance",font=FONT,width=180,height=38,fg_color="#1E3A5F",hover_color="#2563EB",state="disabled",command=self._mark)
        self.mk_btn.pack(side="left",padx=6)
        right=ctk.CTkFrame(body,fg_color=BG2,width=300,corner_radius=8,border_width=1,border_color="#30363D"); right.pack(side="right",fill="y",padx=(16,0)); right.pack_propagate(False)
        ctk.CTkLabel(right,text="TODAY'S ATTENDANCE",font=FONT_SM,text_color=MUTED).pack(anchor="w",padx=14,pady=(14,4))
        self.today_f=ctk.CTkScrollableFrame(right,fg_color=BG2); self.today_f.pack(fill="both",expand=True,padx=6)
        ctk.CTkLabel(right,text="SYSTEM LOG",font=FONT_SM,text_color=MUTED).pack(anchor="w",padx=14,pady=(10,4))
        self.log_box=ctk.CTkTextbox(right,height=160,fg_color=BG,font=("Courier New",9),text_color=MUTED,state="disabled"); self.log_box.pack(fill="x",padx=6,pady=(0,10))
        self._refresh_today(); self._log("System ready. Click Start Camera.")

    def _toggle(self):
        if not self.running:
            if not self.engine.open_camera():
                messagebox.showerror("Error","Could not open camera."); return
            self.running=True
            self.cam_btn.configure(text="⏹  Stop Camera",fg_color="#3D1A1A",hover_color="#7F1D1D")
            self.st_lbl.configure(text="● LIVE",text_color=GREEN)
            self._log("Camera started")
            threading.Thread(target=self._loop,daemon=True).start()
        else:
            self.running=False; self.engine.release_camera()
            self.cam_btn.configure(text="▶  Start Camera",fg_color=GREEN2,hover_color=DIMGREEN)
            self.st_lbl.configure(text="● OFFLINE",text_color=MUTED)
            self.mk_btn.configure(state="disabled")
            self.det.configure(text="[ NO SIGNAL ]",text_color=MUTED); self._log("Camera stopped")

    def _loop(self):
        while self.running and not CameraPage._stop_flag:
            frame=self.engine.read_frame()
            if frame is None: continue
            results=self.engine.identify_faces(frame)
            frame=self.engine.draw_results(frame,results)
            known=[r for r in results if r["id"] is not None]
            if known:
                best=max(known,key=lambda r:r["confidence"]); self.current_match=best
                self.after(0,lambda b=best:self.det.configure(text=f"▶ {b['name'].upper()}  —  {b['confidence']}% match",text_color=GREEN))
                self.after(0,lambda:self.mk_btn.configure(state="normal"))
            else:
                self.current_match=None
                self.after(0,lambda:self.det.configure(text="[ SCANNING... ]" if results else "[ NO FACE DETECTED ]",text_color=AMBER if results else MUTED))
                self.after(0,lambda:self.mk_btn.configure(state="disabled"))
            img=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).resize((640,480))
            photo=ImageTk.PhotoImage(img)
            self.after(0,lambda p=photo:self._upd(p))

    def _upd(self,photo):
        self.vid.configure(image=photo); self.vid.image=photo

    def _mark(self):
        if not self.current_match: return
        marked=db.mark_attendance(self.current_match["id"])
        name=self.current_match["name"]
        if marked: self._log(f"✓ Marked: {name}"); self._refresh_today()
        else: self._log(f"Already marked today: {name}")

    def _refresh_today(self):
        for w in self.today_f.winfo_children(): w.destroy()
        records=db.get_today_attendance()
        if not records:
            ctk.CTkLabel(self.today_f,text="No records yet",font=FONT_SM,text_color=MUTED).pack(pady=10); return
        for r in records:
            row=ctk.CTkFrame(self.today_f,fg_color=BG3,corner_radius=6,height=36); row.pack(fill="x",pady=2); row.pack_propagate(False)
            ctk.CTkLabel(row,text=r["name"][:20],font=FONT_SM,text_color=TEXT).pack(side="left",padx=10)
            ctk.CTkLabel(row,text=r["time"],font=FONT_SM,text_color=GREEN).pack(side="right",padx=10)

    def _log(self,msg):
        t=datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal"); self.log_box.insert("end",f"[{t}] {msg}\n"); self.log_box.see("end"); self.log_box.configure(state="disabled")


# ─── STUDENTS PAGE ───────────────────────────────────────────────────────────

class StudentsPage(ctk.CTkFrame):
    def __init__(self,parent,engine):
        super().__init__(parent,fg_color=BG); self.engine=engine; self._build()

    def _build(self):
        hdr=ctk.CTkFrame(self,fg_color=BG2,height=52,corner_radius=0); hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr,text="STUDENT MANAGEMENT",font=FONT_LG,text_color=GREEN).pack(side="left",padx=20)
        ctk.CTkButton(hdr,text="+ Register New Student",font=FONT,height=34,fg_color=GREEN2,hover_color=DIMGREEN,command=self._open_reg).pack(side="right",padx=20)
        body=ctk.CTkFrame(self,fg_color=BG); body.pack(fill="both",expand=True,padx=16,pady=16)
        sb=ctk.CTkFrame(body,fg_color=BG); sb.pack(fill="x",pady=(0,10))
        ctk.CTkLabel(sb,text="Search:",font=FONT_SM,text_color=MUTED).pack(side="left")
        self.sv=tk.StringVar(); self.sv.trace("w",lambda *a:self._refresh())
        ctk.CTkEntry(sb,textvariable=self.sv,placeholder_text="Name or roll no...",font=FONT,height=34,width=300,fg_color=BG3,border_color="#30363D").pack(side="left",padx=10)
        self.cl=ctk.CTkLabel(sb,text="",font=FONT_SM,text_color=MUTED); self.cl.pack(side="right")
        style=ttk.Style(); style.theme_use("clam")
        style.configure("Dark.Treeview",background=BG3,foreground=TEXT,fieldbackground=BG3,rowheight=32,borderwidth=0)
        style.configure("Dark.Treeview.Heading",background=BG2,foreground=MUTED,relief="flat",font=("Courier New",10))
        style.map("Dark.Treeview",background=[("selected","#1F3A2D")],foreground=[("selected",GREEN)])
        cols=("id","name","roll","dept","enrolled","today")
        self.tree=ttk.Treeview(body,columns=cols,show="headings",style="Dark.Treeview",selectmode="browse")
        for col,text,w in [("id","#",50),("name","Name",220),("roll","Roll No",120),("dept","Department",160),("enrolled","Registered",160),("today","Today",80)]:
            self.tree.heading(col,text=text); self.tree.column(col,width=w,anchor="center" if col!="name" else "w")
        vsb=ttk.Scrollbar(body,orient="vertical",command=self.tree.yview); self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right",fill="y"); self.tree.pack(fill="both",expand=True)
        ctk.CTkButton(body,text="✕  Delete Selected",font=FONT_SM,height=32,width=160,fg_color="#3D1A1A",hover_color="#7F1D1D",command=self._delete).pack(anchor="e",pady=(10,0))
        self._refresh()

    def _refresh(self):
        q=self.sv.get().lower(); students=db.get_all_students()
        today_att={r["name"] for r in db.get_today_attendance()}
        self.tree.delete(*self.tree.get_children()); shown=0
        for s in students:
            if q and q not in s["name"].lower() and q not in (s["roll_no"] or "").lower(): continue
            self.tree.insert("","end",iid=str(s["id"]),values=(s["id"],s["name"],s["roll_no"] or "—",s["department"] or "—",s["created_at"][:10] if s["created_at"] else "—","✓" if s["name"] in today_att else "—")); shown+=1
        self.cl.configure(text=f"{shown} student(s)")

    def _open_reg(self): RegisterDialog(self,self.engine,on_done=self._refresh)

    def _delete(self):
        sel=self.tree.selection()
        if not sel: messagebox.showinfo("Select","Select a student first."); return
        name=self.tree.item(sel[0])["values"][1]
        if messagebox.askyesno("Confirm",f"Delete {name}? This removes all their attendance records."):
            db.delete_student(int(sel[0])); self.engine.reload(); self._refresh()


# ─── REGISTER DIALOG ─────────────────────────────────────────────────────────

class RegisterDialog(ctk.CTkToplevel):
    def __init__(self,parent,engine,on_done=None):
        super().__init__(parent); self.engine=engine; self.on_done=on_done
        self.encoding=None; self.cap_running=False
        self.title("Register New Student"); self.geometry("900x560"); self.configure(fg_color=BG); self.grab_set(); self._build()
        self.after(200,self._start_preview)

    def _build(self):
        ctk.CTkLabel(self,text="REGISTER NEW STUDENT",font=FONT_LG,text_color=GREEN).pack(pady=(16,10))
        body=ctk.CTkFrame(self,fg_color=BG); body.pack(fill="both",expand=True,padx=20)
        left=ctk.CTkFrame(body,fg_color=BG); left.pack(side="left",fill="both",expand=True)
        self.pv=ctk.CTkLabel(left,text="",fg_color="#000",width=480,height=360); self.pv.pack()
        self.fs=ctk.CTkLabel(left,text="[ Position face in frame ]",font=FONT,text_color=MUTED); self.fs.pack(pady=8)
        ctk.CTkButton(left,text="📷  Capture Face Encoding",font=FONT,height=40,fg_color=GREEN2,hover_color=DIMGREEN,command=self._capture).pack()
        right=ctk.CTkFrame(body,fg_color=BG2,width=340,corner_radius=8,border_width=1,border_color="#30363D"); right.pack(side="right",fill="y",padx=(20,0)); right.pack_propagate(False)
        self.fv={}
        for label,key in [("Full Name *","name"),("Roll Number","roll"),("Department","dept")]:
            ctk.CTkLabel(right,text=label,font=FONT_SM,text_color=MUTED).pack(anchor="w",padx=16,pady=(14,2))
            v=tk.StringVar()
            ctk.CTkEntry(right,textvariable=v,font=FONT,fg_color=BG3,border_color="#30363D",height=38).pack(padx=16,fill="x")
            self.fv[key]=v
        self.cl=ctk.CTkLabel(right,text="⚠  Face not captured yet",font=FONT_SM,text_color=AMBER); self.cl.pack(pady=(20,0))
        ctk.CTkButton(right,text="✓  Save Student",font=FONT_LG,height=44,fg_color=GREEN2,hover_color=DIMGREEN,command=self._save).pack(padx=16,pady=16,fill="x",side="bottom")

    def _start_preview(self):
        self.engine.open_camera(); self.cap_running=True
        threading.Thread(target=self._prev_loop,daemon=True).start()

    def _prev_loop(self):
        import face_recognition as fr
        while self.cap_running:
            frame=self.engine.read_frame()
            if frame is None: continue
            rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB); locs=fr.face_locations(rgb,model="hog")
            for t,r,b,l in locs: cv2.rectangle(frame,(l,t),(r,b),(0,255,136),2)
            img=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).resize((480,360))
            photo=ImageTk.PhotoImage(img)
            self.after(0,lambda p=photo:self._upd_pv(p))

    def _upd_pv(self,photo):
        self.pv.configure(image=photo); self.pv.image=photo

    def _capture(self):
        frame=self.engine.read_frame()
        if frame is None: self.fs.configure(text="Camera not available",text_color=RED); return
        enc,_,err=self.engine.capture_encoding_from_frame(frame)
        if err: self.fs.configure(text=f"✗  {err}",text_color=RED); return
        self.encoding=enc; self.fs.configure(text="✓  Face captured!",text_color=GREEN); self.cl.configure(text="✓  Ready to save",text_color=GREEN)

    def _save(self):
        name=self.fv["name"].get().strip()
        if not name: messagebox.showerror("Error","Name is required.",parent=self); return
        if self.encoding is None: messagebox.showerror("Error","Capture face encoding first.",parent=self); return
        db.add_student(name,self.fv["roll"].get().strip() or None,self.fv["dept"].get().strip() or None,self.encoding)
        self.engine.reload(); messagebox.showinfo("Success",f"{name} registered!",parent=self)
        if self.on_done: self.on_done()
        self.destroy()

    def destroy(self):
        self.cap_running=False; self.engine.release_camera(); super().destroy()


# ─── DASHBOARD PAGE ──────────────────────────────────────────────────────────

class DashboardPage(ctk.CTkFrame):
    def __init__(self,parent):
        super().__init__(parent,fg_color=BG); self._build()

    def _build(self):
        hdr=ctk.CTkFrame(self,fg_color=BG2,height=52,corner_radius=0); hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr,text="DASHBOARD  /  ANALYTICS",font=FONT_LG,text_color=GREEN).pack(side="left",padx=20)
        ctk.CTkButton(hdr,text="↺  Refresh",font=FONT_SM,height=30,width=100,fg_color=BG3,hover_color="#30363D",command=self._refresh).pack(side="right",padx=20)
        self.body=ctk.CTkFrame(self,fg_color=BG); self.body.pack(fill="both",expand=True,padx=16,pady=16); self._refresh()

    def _refresh(self):
        for w in self.body.winfo_children(): w.destroy()
        total,present,absent=db.get_dashboard_counts()
        rate=round(present/total*100) if total else 0
        cr=ctk.CTkFrame(self.body,fg_color=BG); cr.pack(fill="x",pady=(0,16))
        for label,val,color in [("TOTAL STUDENTS",total,BLUE),("PRESENT TODAY",present,GREEN),("ABSENT TODAY",absent,RED),("ATTENDANCE RATE",f"{rate}%",AMBER)]:
            card=ctk.CTkFrame(cr,fg_color=BG2,corner_radius=8,border_width=1,border_color="#30363D"); card.pack(side="left",expand=True,fill="x",padx=6)
            ctk.CTkLabel(card,text=str(val),font=("Courier New",30,"bold"),text_color=color).pack(pady=(18,2))
            ctk.CTkLabel(card,text=label,font=("Courier New",9),text_color=MUTED).pack(pady=(0,16))
        weekly=db.get_weekly_stats()
        fig,(ax1,ax2)=plt.subplots(1,2,figsize=(10,3.8),facecolor=BG2)
        for ax in (ax1,ax2):
            ax.set_facecolor(BG2); ax.tick_params(colors=MUTED,labelsize=8)
            for sp in ax.spines.values(): sp.set_color("#30363D")
        if weekly:
            dates=[d[-5:] for d,_ in weekly]; counts=[c for _,c in weekly]
            bars=ax1.bar(dates,counts,color="#238636",width=0.6)
            ax1.set_title("Weekly Attendance",color=TEXT,fontsize=10,pad=8)
            ax1.set_ylabel("Students Present",color=MUTED,fontsize=8)
            for bar,cnt in zip(bars,counts): ax1.text(bar.get_x()+bar.get_width()/2,bar.get_height()+0.1,str(cnt),ha="center",color=GREEN,fontsize=8)
        else:
            ax1.text(0.5,0.5,"No data yet",transform=ax1.transAxes,ha="center",color=MUTED); ax1.set_title("Weekly Attendance",color=TEXT,fontsize=10)
        if total>0:
            wedges,_=ax2.pie([present,absent],colors=["#238636","#F85149"],startangle=90,wedgeprops={"width":0.55,"edgecolor":BG2})
            ax2.legend(wedges,[f"Present\n{present}",f"Absent\n{absent}"],loc="lower center",ncol=2,fontsize=8,frameon=False,labelcolor=TEXT)
        else:
            ax2.text(0.5,0.5,"No students yet",transform=ax2.transAxes,ha="center",color=MUTED)
        ax2.set_title("Today's Split",color=TEXT,fontsize=10,pad=8)
        plt.tight_layout(pad=2)
        canvas=FigureCanvasTkAgg(fig,master=self.body); canvas.draw(); canvas.get_tk_widget().pack(fill="both",expand=True); plt.close(fig)


# ─── EXPORT PAGE ─────────────────────────────────────────────────────────────

class ExportPage(ctk.CTkFrame):
    def __init__(self,parent):
        super().__init__(parent,fg_color=BG); self._build()

    def _build(self):
        hdr=ctk.CTkFrame(self,fg_color=BG2,height=52,corner_radius=0); hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr,text="EXPORT  /  REPORTS",font=FONT_LG,text_color=GREEN).pack(side="left",padx=20)
        body=ctk.CTkFrame(self,fg_color=BG); body.pack(fill="both",expand=True,padx=40,pady=30)
        for title,desc,widget_fn in [
            ("Daily Export","Export attendance for a specific date as Excel (.xlsx)",self._build_daily),
            ("Date Range Export","Export attendance for a date range",self._build_range),
            ("Send Email Report Now","Send today's attendance report to the configured email",self._build_email),
        ]:
            card=ctk.CTkFrame(body,fg_color=BG2,corner_radius=8,border_width=1,border_color="#30363D"); card.pack(fill="x",pady=(0,16))
            ctk.CTkLabel(card,text=title,font=FONT_LG,text_color=GREEN).pack(anchor="w",padx=20,pady=(18,4))
            ctk.CTkLabel(card,text=desc,font=FONT_SM,text_color=MUTED).pack(anchor="w",padx=20)
            widget_fn(card)

    def _build_daily(self,card):
        r=ctk.CTkFrame(card,fg_color=BG2); r.pack(anchor="w",padx=20,pady=12)
        ctk.CTkLabel(r,text="Date:",font=FONT,text_color=TEXT).pack(side="left")
        self.dd=ctk.CTkEntry(r,width=140,font=FONT,fg_color=BG3,border_color="#30363D"); self.dd.pack(side="left",padx=10); self.dd.insert(0,date.today().isoformat())
        ctk.CTkButton(r,text="⬇  Export Excel",font=FONT,height=36,fg_color=GREEN2,hover_color=DIMGREEN,command=self._exp_daily).pack(side="left")

    def _build_range(self,card):
        r=ctk.CTkFrame(card,fg_color=BG2); r.pack(anchor="w",padx=20,pady=12)
        ctk.CTkLabel(r,text="From:",font=FONT,text_color=TEXT).pack(side="left")
        self.fd=ctk.CTkEntry(r,width=130,font=FONT,fg_color=BG3,border_color="#30363D"); self.fd.pack(side="left",padx=10)
        ctk.CTkLabel(r,text="To:",font=FONT,text_color=TEXT).pack(side="left")
        self.td=ctk.CTkEntry(r,width=130,font=FONT,fg_color=BG3,border_color="#30363D"); self.td.pack(side="left",padx=10); self.td.insert(0,date.today().isoformat())
        ctk.CTkButton(r,text="⬇  Export Excel",font=FONT,height=36,fg_color=GREEN2,hover_color=DIMGREEN,command=self._exp_range).pack(side="left")

    def _build_email(self,card):
        self.em=ctk.CTkLabel(card,text="",font=FONT_SM,text_color=MUTED); self.em.pack(anchor="w",padx=20,pady=(4,0))
        ctk.CTkButton(card,text="✉  Send Email Report",font=FONT,height=36,fg_color="#1E3A5F",hover_color="#2563EB",command=self._send).pack(anchor="w",padx=20,pady=12)

    def _exp_daily(self):
        folder=filedialog.askdirectory(title="Save to folder")
        if not folder: return
        path=export_daily(self.dd.get().strip() or date.today().isoformat(),folder); messagebox.showinfo("Exported",f"Saved:\n{path}")

    def _exp_range(self):
        f,t=self.fd.get().strip(),self.td.get().strip()
        if not f or not t: messagebox.showerror("Error","Enter both dates (YYYY-MM-DD)"); return
        folder=filedialog.askdirectory(title="Save to folder")
        if not folder: return
        path=export_range(f,t,folder); messagebox.showinfo("Exported",f"Saved:\n{path}")

    def _send(self):
        self.em.configure(text="Sending...",text_color=AMBER)
        send_daily_report(on_success=lambda m:self.after(0,lambda:self.em.configure(text=f"✓ {m}",text_color=GREEN)),on_error=lambda e:self.after(0,lambda:self.em.configure(text=f"✗ {e}",text_color=RED)))


# ─── SETTINGS PAGE ───────────────────────────────────────────────────────────

class SettingsPage(ctk.CTkFrame):
    def __init__(self,parent,username):
        super().__init__(parent,fg_color=BG); self.username=username; self._build()

    def _build(self):
        hdr=ctk.CTkFrame(self,fg_color=BG2,height=52,corner_radius=0); hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr,text="SETTINGS",font=FONT_LG,text_color=GREEN).pack(side="left",padx=20)
        sc=ctk.CTkScrollableFrame(self,fg_color=BG); sc.pack(fill="both",expand=True,padx=40,pady=20)
        ctk.CTkLabel(sc,text="Change Password",font=FONT_LG,text_color=GREEN).pack(anchor="w",pady=(10,6))
        ctk.CTkFrame(sc,fg_color="#30363D",height=1).pack(fill="x",pady=(0,10))
        self.op=self._f(sc,"Current Password",show="•"); self.np=self._f(sc,"New Password",show="•"); self.np2=self._f(sc,"Confirm New Password",show="•")
        self.pm=ctk.CTkLabel(sc,text="",font=FONT_SM,text_color=MUTED); self.pm.pack(anchor="w")
        ctk.CTkButton(sc,text="Update Password",font=FONT,height=36,fg_color=GREEN2,hover_color=DIMGREEN,width=180,command=self._chpw).pack(anchor="w",pady=(4,20))
        ctk.CTkLabel(sc,text="Email / SMTP Settings",font=FONT_LG,text_color=GREEN).pack(anchor="w",pady=(10,6))
        ctk.CTkFrame(sc,fg_color="#30363D",height=1).pack(fill="x",pady=(0,10))
        ctk.CTkLabel(sc,text="Use Gmail App Password (Settings → Security → App Passwords).",font=FONT_SM,text_color=MUTED).pack(anchor="w",pady=(0,8))
        self.sh=self._f(sc,"SMTP Host",default=db.get_setting("smtp_host","smtp.gmail.com"))
        self.sp=self._f(sc,"SMTP Port",default=db.get_setting("smtp_port","587"))
        self.su=self._f(sc,"Gmail Address",default=db.get_setting("smtp_user",""))
        self.sw=self._f(sc,"Gmail App Password",show="•",default=db.get_setting("smtp_pass",""))
        self.rt=self._f(sc,"Send Report To (email)",default=db.get_setting("report_to",""))
        self.st=self._f(sc,"Auto-Send Time (HH:MM)",default=db.get_setting("send_time","18:00"))
        self.em=ctk.CTkLabel(sc,text="",font=FONT_SM,text_color=MUTED); self.em.pack(anchor="w")
        ctk.CTkButton(sc,text="Save Email Settings",font=FONT,height=36,fg_color=GREEN2,hover_color=DIMGREEN,width=200,command=self._save_email).pack(anchor="w",pady=(4,20))

    def _f(self,parent,label,show="",default=""):
        ctk.CTkLabel(parent,text=label,font=FONT_SM,text_color=MUTED).pack(anchor="w",pady=(6,2))
        v=tk.StringVar(value=default)
        ctk.CTkEntry(parent,textvariable=v,show=show,font=FONT,height=36,width=360,fg_color=BG3,border_color="#30363D").pack(anchor="w")
        return v

    def _chpw(self):
        if not db.verify_admin(self.username,self.op.get()): self.pm.configure(text="✗ Current password wrong",text_color=RED); return
        if len(self.np.get())<6: self.pm.configure(text="✗ Min 6 characters",text_color=RED); return
        if self.np.get()!=self.np2.get(): self.pm.configure(text="✗ Passwords don't match",text_color=RED); return
        db.change_password(self.username,self.np.get()); self.pm.configure(text="✓ Password updated",text_color=GREEN)

    def _save_email(self):
        for k,v in [("smtp_host",self.sh),("smtp_port",self.sp),("smtp_user",self.su),("smtp_pass",self.sw),("report_to",self.rt),("send_time",self.st)]:
            db.set_setting(k,v.get().strip())
        self.em.configure(text="✓ Email settings saved",text_color=GREEN)


# ─── RUN ─────────────────────────────────────────────────────────────────────

if __name__=="__main__":
    LoginWindow().mainloop()
