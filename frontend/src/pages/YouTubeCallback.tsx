import React from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { CheckCircle, XCircle, Loader } from "lucide-react";
import { exchangeYouTubeCode, prettyError } from "../api/videoApi";
import { Card, Button } from "../components/ui";

export default function YouTubeCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = React.useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = React.useState("");

  React.useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const error = searchParams.get("error");

    if (error) {
      setStatus("error");
      setMessage(`Authorization failed: ${error}`);
      return;
    }

    if (!code || !state) {
      setStatus("error");
      setMessage("Missing authorization code or state");
      return;
    }

    // Exchange the code for tokens
    exchangeYouTubeCode(code, state)
      .then(() => {
        setStatus("success");
        setMessage("YouTube account connected successfully!");
      })
      .catch((e) => {
        setStatus("error");
        setMessage(prettyError(e));
      });
  }, [searchParams]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <Card className="max-w-md w-full text-center py-8">
        {status === "loading" && (
          <>
            <Loader className="w-12 h-12 text-primary-600 mx-auto mb-4 animate-spin" />
            <h2 className="text-xl font-semibold text-slate-900 mb-2">
              Connecting YouTube...
            </h2>
            <p className="text-slate-600">Please wait while we complete the connection.</p>
          </>
        )}

        {status === "success" && (
          <>
            <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-slate-900 mb-2">
              Connected!
            </h2>
            <p className="text-slate-600 mb-6">{message}</p>
            <Button onClick={() => navigate(-1)}>
              Return to Video
            </Button>
          </>
        )}

        {status === "error" && (
          <>
            <XCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-slate-900 mb-2">
              Connection Failed
            </h2>
            <p className="text-red-600 mb-6">{message}</p>
            <div className="flex gap-2 justify-center">
              <Button variant="secondary" onClick={() => navigate("/")}>
                Go to Dashboard
              </Button>
              <Button onClick={() => navigate(-1)}>
                Try Again
              </Button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
