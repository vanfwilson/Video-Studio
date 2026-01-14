import React from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { exchangeYouTubeCode, prettyError } from "../api/videoApi";
import { Card } from "../components/Card";
import { Spinner } from "../components/Spinner";
import { Button } from "../components/Button";
import { useToast } from "../components/Toasts";

export default function YouTubeOAuthCallback() {
  const toast = useToast();
  const nav = useNavigate();
  const [sp] = useSearchParams();
  const [busy, setBusy] = React.useState(true);
  const [err, setErr] = React.useState<string | null>(null);

  React.useEffect(() => {
    const run = async () => {
      const code = sp.get("code");
      const state = sp.get("state") || undefined;

      if (!code) {
        setErr("Missing code in callback URL.");
        setBusy(false);
        return;
      }

      try {
        await exchangeYouTubeCode(code, state);
        toast.push({ type: "success", message: "YouTube connected." });
        nav("/"); // or back to last publish page if you store it
      } catch (e) {
        setErr(prettyError(e));
      } finally {
        setBusy(false);
      }
    };

    run();
  }, [sp, nav, toast]);

  if (busy) return <Spinner label="Finalizing YouTube connection..." />;

  return (
    <Card className={err ? "border-rose-200 bg-rose-50" : ""}>
      {err ? (
        <>
          <div className="text-sm text-rose-800">OAuth error: {err}</div>
          <div className="mt-3">
            <Button variant="secondary" onClick={() => nav("/")}>Back to Dashboard</Button>
          </div>
        </>
      ) : (
        <div className="text-sm text-slate-700">Connected. Redirecting…</div>
      )}
    </Card>
  );
}
