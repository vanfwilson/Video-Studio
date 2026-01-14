// src/components/UserSwitcher.tsx
import React from "react";
import { Button } from "./Button";
import { Input } from "./Field";

export function UserSwitcher() {
  const [userId, setUserId] = React.useState(() => localStorage.getItem("vs_user_id") || "demo-user");
  const [editing, setEditing] = React.useState(false);
  const [tmp, setTmp] = React.useState(userId);

  const save = () => {
    localStorage.setItem("vs_user_id", tmp.trim() || "demo-user");
    setUserId(localStorage.getItem("vs_user_id") || "demo-user");
    setEditing(false);
  };

  return (
    <div className="flex items-center gap-2">
      {!editing ? (
        <>
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-700">
            User: <span className="font-mono">{userId}</span>
          </div>
          <Button variant="secondary" onClick={() => { setTmp(userId); setEditing(true); }}>
            Change
          </Button>
        </>
      ) : (
        <>
          <div className="w-56">
            <Input value={tmp} onChange={(e) => setTmp(e.target.value)} placeholder="user-id (UUID/email/etc.)" />
          </div>
          <Button onClick={save}>Save</Button>
          <Button variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>
        </>
      )}
    </div>
  );
}
