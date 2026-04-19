import os
import struct
import math
import secrets
import time
from flask import Flask, request, jsonify, render_template_string, session, redirect

app = Flask(name)
app.secret_key = secrets.token_hex(16)

# --- SYSTEM CONSTANTS ---
DISK_SIZE = 1048576       
BLOCK_SIZE = 512          
TOTAL_BLOCKS = DISK_SIZE // BLOCK_SIZE 
MAX_INODES = 50           
INODE_FORMAT = '32s i i i i i 10i'    

class Inode:
    def init(self, name="", size=0, is_used=0, owner_id=1000, permissions=0o644, created_at=0, blocks=None):
        self.name = name
        self.size = size
        self.is_used = is_used
        self.owner_id = owner_id        
        self.permissions = permissions  
        self.created_at = created_at if created_at else int(time.time())
        self.blocks = blocks if blocks else [-1] * 10

inodes = [Inode() for _ in range(MAX_INODES)]
bitmap = bytearray(TOTAL_BLOCKS // 8) 

# --- METADATA KERNEL ---
def load_metadata():
    if not os.path.exists("disk.bin"): return
    with open("disk.bin", "rb") as fp:
        fp.seek(BLOCK_SIZE)
        global bitmap
        bitmap = bytearray(fp.read(TOTAL_BLOCKS // 8))
        
        fp.seek(BLOCK_SIZE * 2)
        inode_struct_size = struct.calcsize(INODE_FORMAT)
        for i in range(MAX_INODES):
            chunk = fp.read(inode_struct_size)
            if not chunk: break
            raw_name, size, used, uid, perms, c_at, *block_pointers = struct.unpack(INODE_FORMAT, chunk)
            if used == 1:
                clean_name = raw_name.decode('utf-8', errors='ignore').strip('\x00')
                inodes[i] = Inode(clean_name, size, used, uid, perms, c_at, list(block_pointers))

def sync_metadata():
    with open("disk.bin", "r+b") as fp:
        fp.seek(BLOCK_SIZE)
        fp.write(bitmap)
        fp.seek(BLOCK_SIZE * 2)
        for i in inodes:
            n_bytes = i.name.encode('utf-8')[:32].ljust(32, b'\x00')
            data = struct.pack(INODE_FORMAT, n_bytes, i.size, i.is_used, i.owner_id, i.permissions, i.created_at, *i.blocks)
            fp.write(data)

# --- UTILITIES ---
def is_block_used(n): return (bitmap[n // 8] & (1 << (n % 8))) != 0

def set_block(n, used=True):
    if used: bitmap[n // 8] |= (1 << (n % 8))
    else: bitmap[n // 8] &= ~(1 << (n % 8))

def check_permission(inode, uid, mask):
    if int(inode.owner_id) == int(uid):
        return ((inode.permissions >> 6) & 7 & mask) > 0
    return (inode.permissions & 7 & mask) > 0

# --- PREMIUM UI TEMPLATE ---
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Enterprise VFS Shell</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a; --card: #1e293b; --primary: #6366f1; --primary-hover: #4f46e5;
            --danger: #ef4444; --danger-hover: #dc2626; --text: #f8fafc; --text-muted: #94a3b8;
            --border: #334155; --success: #10b981; --append: #f59e0b;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: var(--bg); color: var(--text); padding: 40px 20px; display: flex; justify-content: center; }
        .container { width: 100%; max-width: 1000px; }
        
        .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .card h2, .card h3 { margin-bottom: 16px; font-weight: 600; color: #fff; display: flex; align-items: center; gap: 8px;}
        
        .navbar { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; background: var(--card); border-radius: 12px; margin-bottom: 24px; border: 1px solid var(--border); }
[4/16/2026 3:20 PM] Laxman: .user-badge { background: rgba(99, 102, 241, 0.1); color: #818cf8; padding: 6px 12px; border-radius: 20px; font-size: 14px; font-weight: 500; border: 1px solid rgba(99, 102, 241, 0.2); }
        
        input, select, textarea { width: 100%; padding: 12px; margin-bottom: 16px; background: #0b1120; border: 1px solid var(--border); color: white; border-radius: 8px; outline: none; font-size: 14px; transition: border 0.2s; }
        input:focus, select:focus, textarea:focus { border-color: var(--primary); }
        textarea { resize: vertical; min-height: 100px; }
        
        button { background: var(--primary); color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: 500; cursor: pointer; transition: all 0.2s; font-size: 14px; }
        button:hover { background: var(--primary-hover); transform: translateY(-1px); }
        .btn-danger { background: var(--danger); }
        .btn-danger:hover { background: var(--danger-hover); }
        .btn-outline { background: transparent; border: 1px solid var(--success); color: var(--success); }
        .btn-outline:hover { background: rgba(16, 185, 129, 0.1); }
        
        .dashboard-grid { display: grid; grid-template-columns: 350px 1fr; gap: 24px; }
        
        .table-container { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th { padding: 12px 16px; background: rgba(0,0,0,0.2); color: var(--text-muted); font-size: 12px; text-transform: uppercase; border-bottom: 1px solid var(--border); }
        td { padding: 16px; border-bottom: 1px solid var(--border); font-size: 14px; color: #cbd5e1; }
        tr:hover td { background: rgba(255,255,255,0.02); }
        .mono { font-family: 'Courier New', monospace; color: #fbbf24; background: rgba(251, 191, 36, 0.1); padding: 2px 6px; border-radius: 4px; }
        
        #toast { position: fixed; bottom: 20px; right: 20px; padding: 16px 24px; border-radius: 8px; color: white; font-weight: 500; transform: translateX(150%); transition: transform 0.3s; z-index: 1000; box-shadow: 0 10px 15px rgba(0,0,0,0.3); }
        .toast-success { background: var(--success); border-left: 4px solid #059669; }
        .toast-error { background: var(--danger); border-left: 4px solid #b91c1c; }
        
        #readModal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px); z-index: 500; align-items: center; justify-content: center; }
        .modal-content { background: var(--card); border: 1px solid var(--border); padding: 24px; border-radius: 12px; width: 500px; max-width: 90%; }
        .modal-body { background: #0b1120; padding: 16px; border-radius: 8px; margin: 16px 0; font-family: monospace; color: #a7f3d0; white-space: pre-wrap; word-wrap: break-word; border: 1px solid var(--border); max-height: 300px; overflow-y: auto;}
    </style>
</head>
<body>

    <div id="toast"></div>

    <div id="readModal">
        <div class="modal-content">
            <h3 id="modalTitle">📄 File Content</h3>
            <div class="modal-body" id="modalText"></div>
            <button onclick="document.getElementById('readModal').style.display='none'" style="width: 100%;">Close Viewer</button>
        </div>
    </div>

    <div class="container">
        {% if not session.get('uid') %}
        <div class="card" style="max-width: 400px; margin: 10vh auto; text-align: center;">
            <div style="width: 48px; height: 48px; background: var(--primary); border-radius: 12px; margin: 0 auto 16px; display: flex; align-items: center; justify-content: center; font-size: 24px;">🛡️</div>
            <h2>System Authentication</h2>
            <p style="color: var(--text-muted); margin-bottom: 24px; font-size: 14px;">Please log in to access the Virtual File System.</p>
[4/16/2026 3:20 PM] Laxman: <form method="POST" action="/login">
                <input type="text" name="user" placeholder="Enter Username" required>
                <select name="uid">
                    <option value="1000">Administrator (UID: 1000)</option>
                    <option value="1001">Standard Guest (UID: 1001)</option>
                </select>
                <button type="submit" style="width: 100%; padding: 12px;">Authenticate Session</button>
            </form>
        </div>
        {% else %}
        
        <div class="navbar">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 24px;">🚀</span>
                <h2 style="margin: 0; font-size: 18px;">Enterprise VFS Kernel</h2>
            </div>
            <div style="display: flex; align-items: center; gap: 16px;">
                <span class="user-badge">👤 {{ session['user'] }} ({{ session['uid'] }})</span>
                <a href="/logout" style="color: var(--text-muted); text-decoration: none; font-size: 14px; transition: color 0.2s;" onmouseover="this.style.color='#ef4444'" onmouseout="this.style.color='#94a3b8'">Log Out</a>
            </div>
        </div>

        <div class="dashboard-grid">
            <div class="operations-col">
                <div class="card">
                    <h3>📝 Initialize File</h3>
                    <input type="text" id="fn" placeholder="file_name.txt" autocomplete="off">
                    <textarea id="fc" placeholder="Enter file data here..."></textarea>
                    <button onclick="save()" style="width: 100%; margin-bottom: 12px;">Commit to Disk</button>
                </div>
                
                <div class="card" style="border-color: rgba(239, 68, 68, 0.3);">
                    <h3>⚠️ Danger Zone</h3>
                    <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">Wiping the disk will permanently delete all data.</p>
                    <button onclick="fmt()" class="btn-danger" style="width: 100%;">Format Entire Drive</button>
                </div>
            </div>

            <div class="card" style="margin-bottom: 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h3 style="margin: 0;">📂 File Explorer</h3>
                    <button class="btn-outline" onclick="load()" style="padding: 6px 12px; font-size: 12px; border-color: var(--border); color: var(--text);">🔄 Refresh</button>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Filename</th>
                                <th>Size</th>
                                <th>Perms</th>
                                <th style="text-align: right;">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="list"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            function showToast(message, isError = false) {
                const toast = document.getElementById('toast');
                toast.textContent = message;
                toast.className = isError ? 'toast-error' : 'toast-success';
                toast.style.transform = 'translateX(0)';
                setTimeout(() => { toast.style.transform = 'translateX(150%)'; }, 3000);
            }

            async function load(){
                try {
                    const r = await fetch('/api/list');
                    const d = await r.json();
                    const tbody = document.getElementById('list');
                    
                    if(d.files.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #64748b; padding: 32px;">No files allocated on disk.</td></tr>';
                        return;
                    }
[4/16/2026 3:20 PM] Laxman: tbody.innerHTML = d.files.map(f => 
                        <tr>
                            <td style="font-weight: 500; color: #fff;">${f.name}</td>
                            <td style="color: #94a3b8;">${f.size} B</td>
                            <td><span class="mono">${f.perms}</span></td>
                            <td style="text-align: right;">
                                <button onclick="read('${f.name}')" style="padding: 6px 10px; font-size: 12px;">Read</button> 
                                <button onclick="appendF('${f.name}')" class="btn-outline" style="padding: 6px 10px; font-size: 12px;">Append</button> 
                                <button onclick="del('${f.name}')" class="btn-danger" style="padding: 6px 10px; font-size: 12px;">Del</button>
                            </td>
                        </tr>).join('');
                } catch(e) { showToast("Failed to fetch filesystem", true); }
            }

            async function save(){
                const n = document.getElementById('fn').value;
                const c = document.getElementById('fc').value;
                if(!n) return showToast("Filename required", true);
                
                const r = await fetch('/api/save', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({n, c})});
                const res = await r.json();
                
                if(res.error) showToast(res.error, true);
                else {
                    showToast(File ${n} saved securely.);
                    document.getElementById('fn').value = '';
                    document.getElementById('fc').value = '';
                    load();
                }
            }

            async function appendF(n) {
                const text = prompt(Enter text to append to ${n}:);
                if(!text) return;
                
                const r = await fetch('/api/append', {
                    method:'POST', 
                    headers:{'Content-Type':'application/json'}, 
                    body:JSON.stringify({n: n, c: text})
                });
                const res = await r.json();
                
                if(res.error) showToast(res.error, true);
                else { showToast(Appended to ${n} successfully.); load(); }
            }

            async function read(n){ 
                const r = await fetch('/api/read/'+n);
                const res = await r.json();
                if(res.error) {
                    showToast(res.error, true);
                } else {
                    document.getElementById('modalTitle').innerHTML = 📄 ${n};
                    document.getElementById('modalText').textContent = res.content;
                    document.getElementById('readModal').style.display = 'flex';
                }
            }

            async function del(n){ 
                if(!confirm(Delete ${n}?)) return;
                const r = await fetch('/api/del', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({n})});
                const res = await r.json();
                if(res.error) showToast(res.error, true);
                else { showToast(Deleted ${n}); load(); }
            }

            async function fmt(){ 
                if(!confirm('CRITICAL WARNING: This will wipe the entire virtual disk. Proceed?')) return;
                const r = await fetch('/api/fmt', {method:'POST'});
                if(r.ok) { showToast("Disk formatted successfully."); load(); }
            }

            window.onload = load;
        </script>
        {% endif %}
    </div>
</body>
</html>
"""

# --- API ROUTES ---
@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/login', methods=['POST'])
def login():
    session['user'], session['uid'] = request.form.get('user'), int(request.form.get('uid'))
    return redirect('/')

@app.route('/logout')
def logout(): session.clear(); return redirect('/')
@app.route('/api/save', methods=['POST'])
def save_file():
    data = request.json
    n, c = data['n'].strip(), data['c'].encode('utf-8')
    if any(i.is_used and i.name == n for i in inodes): return jsonify({"error": "File already exists"}), 400
    
    blocks_needed = math.ceil(len(c) / 512) or 1
    free_blocks = []
    for i in range(10, TOTAL_BLOCKS):
        if not is_block_used(i):
            free_blocks.append(i)
            if len(free_blocks) == blocks_needed: break
    
    free_inode = next((i for i in inodes if i.is_used == 0), None)
    
    if free_inode and len(free_blocks) == blocks_needed:
        with open("disk.bin", "r+b") as f:
            for i, b in enumerate(free_blocks):
                set_block(b, True); f.seek(b*512); f.write(c[i*512:(i+1)*512])
            free_inode.name, free_inode.size, free_inode.is_used = n, len(c), 1
            free_inode.owner_id, free_inode.created_at = session['uid'], int(time.time())
            free_inode.blocks = free_blocks + [-1]*(10-len(free_blocks))
            sync_metadata()
    else: return jsonify({"error": "Not enough disk space"}), 500
    return jsonify({"ok":True})

# --- NEW APPEND ROUTE ---
@app.route('/api/append', methods=['POST'])
def append_file():
    data = request.json
    n, append_content = data['n'], data['c'].encode('utf-8')
    
    i = next((x for x in inodes if x.is_used and x.name == n), None)
    if not i: return jsonify({"error":"File not found"}), 404
    if not check_permission(i, session['uid'], 2): return jsonify({"error":"Write Access Denied"}), 403
    
    # Read existing content
    content = b""
    with open("disk.bin", "rb") as f:
        for b in i.blocks:
            if b == -1: break
            f.seek(b * 512); content += f.read(512)
    
    existing_content = content[:i.size]
    new_content = existing_content + append_content # Combine old and new
    
    blocks_needed = math.ceil(len(new_content) / 512) or 1
    if blocks_needed > 10: return jsonify({"error": "File exceeds maximum allowed size (5KB)"}), 400
    
    current_blocks = [b for b in i.blocks if b != -1]
    extra_needed = blocks_needed - len(current_blocks)
    
    new_blocks = []
    if extra_needed > 0:
        for b_idx in range(10, TOTAL_BLOCKS):
            if not is_block_used(b_idx):
                new_blocks.append(b_idx)
                if len(new_blocks) == extra_needed: break
        if len(new_blocks) < extra_needed: return jsonify({"error": "Disk Full"}), 500
        
    all_blocks = current_blocks + new_blocks
    
    with open("disk.bin", "r+b") as f:
        for b in new_blocks: set_block(b, True) # Mark new blocks as used
        
        # Rewrite the file across all allocated blocks
        for idx, b in enumerate(all_blocks):
            f.seek(b * 512)
            f.write(new_content[idx*512:(idx+1)*512])
            
        i.size = len(new_content)
        i.blocks = all_blocks + [-1]*(10-len(all_blocks))
        sync_metadata()
        
    return jsonify({"ok":True})

@app.route('/api/list')
def list_files():
    return jsonify({"files": [{"name":i.name, "owner":i.owner_id, "perms":oct(i.permissions)[2:], "size":i.size, "date":i.created_at} for i in inodes if i.is_used]})

@app.route('/api/read/<name>')
def read_file(name):
    i = next((x for x in inodes if x.is_used and x.name == name), None)
    if not i: return jsonify({"error":"File not found"})
    if not check_permission(i, session['uid'], 4): return jsonify({"error":"Read Access Denied by Kernel"})
    
    content = b""
    with open("disk.bin", "rb") as f:
        for b in i.blocks:
            if b == -1: break
            f.seek(b*512); content += f.read(512)
    return jsonify({"content": content[:i.size].decode('utf-8', errors='ignore')})

@app.route('/api/del', methods=['POST'])
def del_file():
    n = request.json['n']
    i = next((x for x in inodes if x.is_used and x.name == n), None)
    if not i: return jsonify({"error":"File not found"})
    if not check_permission(i, session['uid'], 2): return jsonify({"error":"Write Access Denied by Kernel"})
    
    for b in i.blocks:
        if b != -1: set_block(b, False)
    i.is_used = 0
    sync_metadata()
    return jsonify({"ok":True})

@app.route('/api/fmt', methods=['POST'])
def format_disk():
    global bitmap
    bitmap = bytearray(TOTAL_BLOCKS // 8)
    with open("disk.bin", "wb") as f: f.write(b'\0' * DISK_SIZE)
        for i in range(MAX_INODES): inodes[i] = Inode()
    sync_metadata()
    return jsonify({"ok": True})

if __name__ =='__main__':
    if not os.path.exists("disk.bin"):
        with open("disk.bin", "wb") as f: f.write(b'\0'*DISK_SIZE)
        load_metadata()
        app.run(debug=True, port=5000)