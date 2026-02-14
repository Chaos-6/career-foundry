/**
 * Upgrade prompt dialog — shown when a free user hits their tier limit.
 *
 * This is a reusable component that can be triggered from anywhere
 * (evaluation creation, mock interview, etc.) when the API returns
 * a TIER_LIMIT_REACHED error.
 *
 * Detection pattern:
 *   catch (err) {
 *     if (err?.response?.status === 403 && err?.response?.data?.detail?.code === "TIER_LIMIT_REACHED") {
 *       setShowUpgrade(true);
 *     }
 *   }
 */

import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  Typography,
} from "@mui/material";
import RocketLaunchIcon from "@mui/icons-material/RocketLaunch";

interface UpgradePromptProps {
  open: boolean;
  onClose: () => void;
  currentUsage?: number;
  limit?: number;
}

export default function UpgradePrompt({
  open,
  onClose,
  currentUsage,
  limit,
}: UpgradePromptProps) {
  const navigate = useNavigate();

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ fontWeight: 700 }}>
        Monthly Limit Reached
      </DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          <Typography>
            You've used {currentUsage ?? "all"} of your{" "}
            {limit ?? 5} free evaluations this month.
          </Typography>
          <Typography color="text.secondary">
            Upgrade to <strong>Pro</strong> for unlimited evaluations,
            advanced analytics, PDF reports, and more.
          </Typography>
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2, pt: 0 }}>
        <Button onClick={onClose} color="inherit">
          Maybe Later
        </Button>
        <Button
          variant="contained"
          startIcon={<RocketLaunchIcon />}
          onClick={() => {
            onClose();
            navigate("/pricing");
          }}
        >
          View Plans
        </Button>
      </DialogActions>
    </Dialog>
  );
}

/**
 * Helper to detect tier limit errors from API responses.
 * Use this in catch blocks to determine whether to show the upgrade prompt.
 */
export function isTierLimitError(err: any): {
  isLimit: boolean;
  currentUsage?: number;
  limit?: number;
} {
  if (
    err?.response?.status === 403 &&
    err?.response?.data?.detail?.code === "TIER_LIMIT_REACHED"
  ) {
    return {
      isLimit: true,
      currentUsage: err.response.data.detail.current_usage,
      limit: err.response.data.detail.limit,
    };
  }
  return { isLimit: false };
}
