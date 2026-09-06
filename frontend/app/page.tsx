import HiLoGame from "@/components/hi-lo/HiLoGame";
import RequireAuth from "@/components/auth/RequireAuth";

export default function HiLoPage() {
  return (
    <RequireAuth>
      <HiLoGame />
    </RequireAuth>
  );
}
