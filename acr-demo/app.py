from datetime import datetime, timezone
import json
import os
from pathlib import Path
from threading import Lock
from uuid import uuid4

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
DATA_FILE = Path(__file__).with_name("users.json")
DATA_LOCK = Lock()


def ensure_data_file():
    """Create the temporary JSON store only when it does not already exist."""
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]\n", encoding="utf-8")


def read_users():
    ensure_data_file()
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def write_users(users):
    temporary_file = DATA_FILE.with_suffix(".json.tmp")
    temporary_file.write_text(
        json.dumps(users, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary_file.replace(DATA_FILE)


def validate_user(payload):
    name = str(payload.get("name", "")).strip()
    mobile = str(payload.get("mobile", "")).strip()
    if not name:
        return None, "User name is required."
    if not mobile:
        return None, "Mobile number is required."
    digits = "".join(character for character in mobile if character.isdigit())
    if not 7 <= len(digits) <= 15:
        return None, "Enter a valid mobile number containing 7 to 15 digits."
    return {"name": name, "mobile": mobile}, None


ensure_data_file()

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Azure Container Registry Demo</title>
    <style>
        :root { --primary:#2563eb; --primary-hover:#1d4ed8; --danger:#dc2626; --page:#f4f7fb; --surface:#fff; --border:#e2e8f0; --text:#172033; --muted:#64748b; }
        * { box-sizing:border-box; }
        body { margin:0; min-height:100vh; padding:48px 24px; color:var(--text); background:var(--page); font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
        .container { width:min(960px,100%); margin:auto; overflow:hidden; background:var(--surface); border:1px solid var(--border); border-radius:16px; box-shadow:0 16px 40px rgba(15,23,42,.08); }
        .header { display:flex; align-items:center; justify-content:space-between; gap:20px; padding:24px 28px; border-bottom:1px solid var(--border); }
        h1 { margin:0; font-size:clamp(22px,4vw,30px); line-height:1.2; }
        button { font:inherit; }
        .btn { display:inline-flex; align-items:center; justify-content:center; gap:8px; min-height:42px; padding:9px 16px; color:#fff; background:var(--primary); border:0; border-radius:8px; font-weight:700; cursor:pointer; transition:.15s; }
        .btn:hover { background:var(--primary-hover); transform:translateY(-1px); }
        .btn:disabled { cursor:not-allowed; opacity:.65; transform:none; }
        .btn-secondary { color:var(--text); background:#e2e8f0; }
        .btn-secondary:hover { background:#cbd5e1; }
        .table-wrap { padding:24px 28px 30px; overflow-x:auto; }
        table { width:100%; border-collapse:collapse; }
        th,td { padding:14px 16px; border-bottom:1px solid var(--border); text-align:left; }
        th { color:#475569; background:#f8fafc; font-size:13px; text-transform:uppercase; letter-spacing:.04em; }
        tbody tr:hover { background:#f8fafc; }
        .actions { display:flex; gap:8px; }
        .icon-btn { width:38px; height:38px; display:inline-grid; place-items:center; color:var(--primary); background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; cursor:pointer; }
        .icon-btn:hover { background:#dbeafe; }
        .icon-btn.delete { color:var(--danger); background:#fef2f2; border-color:#fecaca; }
        .icon-btn.delete:hover { background:#fee2e2; }
        .icon { width:18px; height:18px; fill:none; stroke:currentColor; stroke-linecap:round; stroke-linejoin:round; stroke-width:2; }
        .empty-state { padding:44px 16px; color:var(--muted); text-align:center; }
        .modal-backdrop { position:fixed; inset:0; z-index:20; display:none; align-items:center; justify-content:center; padding:20px; background:rgba(15,23,42,.62); }
        .modal-backdrop.open { display:flex; }
        .modal { width:min(460px,100%); padding:26px; background:#fff; border-radius:14px; box-shadow:0 24px 70px rgba(0,0,0,.25); }
        .modal h2 { margin:0 0 22px; font-size:22px; }
        .field { margin-bottom:17px; }
        label { display:block; margin-bottom:7px; font-size:14px; font-weight:700; }
        input { width:100%; padding:11px 12px; color:var(--text); border:1px solid #cbd5e1; border-radius:8px; font:inherit; outline:none; }
        input:focus { border-color:var(--primary); box-shadow:0 0 0 3px rgba(37,99,235,.14); }
        .error { min-height:20px; margin:-4px 0 12px; color:var(--danger); font-size:13px; }
        .modal-actions { display:flex; justify-content:flex-end; gap:10px; }
        .toast { position:fixed; right:24px; bottom:24px; z-index:30; display:none; max-width:360px; padding:12px 16px; color:#fff; background:#15803d; border-radius:8px; box-shadow:0 10px 30px rgba(0,0,0,.2); }
        .toast.show { display:block; }
        .toast.error-toast { background:var(--danger); }
        @media(max-width:600px) { body{padding:20px 12px}.header{align-items:flex-start;flex-direction:column;padding:20px}.header .btn{width:100%}.table-wrap{padding:18px 14px 24px}th,td{padding:12px 10px} }
    </style>
</head>
<body>
    <main class="container">
        <header class="header">
            <h1>Azure Container Registry Demo</h1>
            <button class="btn" type="button" onclick="openModal()">
                <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg> Add User
            </button>
        </header>
        <section class="table-wrap" aria-label="User details">
            <table><thead><tr><th>User Name</th><th>Mobile Number</th><th>Actions</th></tr></thead><tbody id="user-table-body"></tbody></table>
            <div id="empty-state" class="empty-state">No user details added yet.</div>
        </section>
    </main>

    <div id="user-modal" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="modal-title" onclick="closeOnBackdrop(event)">
        <form class="modal" id="user-form">
            <h2 id="modal-title">Add User Details</h2>
            <div class="field"><label for="user-name">User Name</label><input id="user-name" type="text" maxlength="100" autocomplete="name" required></div>
            <div class="field"><label for="mobile-number">Mobile Number</label><input id="mobile-number" type="tel" maxlength="20" autocomplete="tel" placeholder="e.g. +91 98765 43210" required></div>
            <div id="form-error" class="error" role="alert"></div>
            <div class="modal-actions"><button class="btn btn-secondary" type="button" onclick="closeModal()">Cancel</button><button class="btn" id="submit-button" type="submit">Submit</button></div>
        </form>
    </div>
    <div id="toast" class="toast" role="status"></div>

    <script>
        const editIcon='<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z"/></svg>';
        const deleteIcon='<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v5M14 11v5"/></svg>';
        let users=[]; let editingId=null;
        function escapeHtml(value){const element=document.createElement('div');element.textContent=value;return element.innerHTML;}
        async function loadUsers(){try{const response=await fetch('/api/users');if(!response.ok)throw new Error('Unable to load users.');users=await response.json();renderUsers();}catch(error){showToast(error.message,true);}}
        function renderUsers(){
            const body=document.getElementById('user-table-body');
            body.innerHTML=users.map(user=>`<tr><td>${escapeHtml(user.name)}</td><td>${escapeHtml(user.mobile)}</td><td><div class="actions"><button class="icon-btn" type="button" title="Edit user" aria-label="Edit ${escapeHtml(user.name)}" onclick="openModal('${user.id}')">${editIcon}</button><button class="icon-btn delete" type="button" title="Delete user" aria-label="Delete ${escapeHtml(user.name)}" onclick="deleteUser('${user.id}')">${deleteIcon}</button></div></td></tr>`).join('');
            document.getElementById('empty-state').style.display=users.length?'none':'block';
        }
        function openModal(id=null){editingId=id;const user=users.find(item=>item.id===id);document.getElementById('modal-title').textContent=user?'Edit User Details':'Add User Details';document.getElementById('submit-button').textContent=user?'Update':'Submit';document.getElementById('user-name').value=user?.name||'';document.getElementById('mobile-number').value=user?.mobile||'';document.getElementById('form-error').textContent='';document.getElementById('user-modal').classList.add('open');setTimeout(()=>document.getElementById('user-name').focus(),0);}
        function closeModal(){editingId=null;document.getElementById('user-form').reset();document.getElementById('form-error').textContent='';document.getElementById('user-modal').classList.remove('open');}
        function closeOnBackdrop(event){if(event.target===event.currentTarget)closeModal();}
        document.addEventListener('keydown',event=>{if(event.key==='Escape')closeModal();});
        document.getElementById('user-form').addEventListener('submit',async event=>{
            event.preventDefault();const idToUpdate=editingId;const button=document.getElementById('submit-button');const errorElement=document.getElementById('form-error');
            const payload={name:document.getElementById('user-name').value.trim(),mobile:document.getElementById('mobile-number').value.trim()};button.disabled=true;errorElement.textContent='';
            try{const response=await fetch(idToUpdate?`/api/users/${idToUpdate}`:'/api/users',{method:idToUpdate?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const result=await response.json();if(!response.ok)throw new Error(result.error||'Unable to save user.');closeModal();await loadUsers();showToast(idToUpdate?'User updated.':'User added.');}catch(error){errorElement.textContent=error.message;}finally{button.disabled=false;}
        });
        async function deleteUser(id){const user=users.find(item=>item.id===id);if(!user||!confirm(`Delete ${user.name}?`))return;try{const response=await fetch(`/api/users/${id}`,{method:'DELETE'});const result=await response.json();if(!response.ok)throw new Error(result.error||'Unable to delete user.');await loadUsers();showToast('User deleted.');}catch(error){showToast(error.message,true);}}
        function showToast(message,isError=false){const toast=document.getElementById('toast');toast.textContent=message;toast.className=`toast show${isError?' error-toast':''}`;clearTimeout(showToast.timer);showToast.timer=setTimeout(()=>toast.className='toast',2600);}
        loadUsers();
    </script>
</body>
</html>"""


@app.get("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.get("/api/users")
def get_users():
    with DATA_LOCK:
        return jsonify(read_users())


@app.post("/api/users")
def create_user():
    validated, error = validate_user(request.get_json(silent=True) or {})
    if error:
        return jsonify({"error": error}), 400
    new_user = {"id": uuid4().hex, **validated}
    with DATA_LOCK:
        users = read_users()
        users.append(new_user)
        write_users(users)
    return jsonify(new_user), 201


@app.put("/api/users/<user_id>")
def update_user(user_id):
    validated, error = validate_user(request.get_json(silent=True) or {})
    if error:
        return jsonify({"error": error}), 400
    with DATA_LOCK:
        users = read_users()
        user = next((item for item in users if item.get("id") == user_id), None)
        if user is None:
            return jsonify({"error": "User not found."}), 404
        user.update(validated)
        write_users(users)
    return jsonify(user)


@app.delete("/api/users/<user_id>")
def delete_user(user_id):
    with DATA_LOCK:
        users = read_users()
        remaining_users = [item for item in users if item.get("id") != user_id]
        if len(remaining_users) == len(users):
            return jsonify({"error": "User not found."}), 404
        write_users(remaining_users)
    return jsonify({"message": "User deleted."})


@app.get("/api/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
