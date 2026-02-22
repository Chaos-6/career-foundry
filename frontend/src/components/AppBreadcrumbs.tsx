/**
 * Reusable breadcrumb component using MUI Breadcrumbs.
 *
 * Usage:
 *   <AppBreadcrumbs crumbs={[
 *     { label: "Dashboard", path: "/" },
 *     { label: "Evaluation Results" },  // no path → current page (plain text)
 *   ]} />
 *
 * The last crumb renders as plain text (the current page).
 * All others render as clickable links that navigate via React Router.
 */

import React from "react";
import { useNavigate } from "react-router-dom";
import { Breadcrumbs, Link, Typography } from "@mui/material";
import NavigateNextIcon from "@mui/icons-material/NavigateNext";

export interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface Props {
  crumbs: BreadcrumbItem[];
}

export default function AppBreadcrumbs({ crumbs }: Props) {
  const navigate = useNavigate();

  if (crumbs.length === 0) return null;

  return (
    <Breadcrumbs
      separator={<NavigateNextIcon fontSize="small" />}
      sx={{ mb: 2 }}
      aria-label="breadcrumb"
    >
      {crumbs.map((crumb, i) => {
        const isLast = i === crumbs.length - 1;

        if (isLast || !crumb.path) {
          return (
            <Typography
              key={crumb.label}
              color="text.primary"
              variant="body2"
              fontWeight={isLast ? 600 : 400}
            >
              {crumb.label}
            </Typography>
          );
        }

        return (
          <Link
            key={crumb.label}
            color="text.secondary"
            underline="hover"
            variant="body2"
            sx={{ cursor: "pointer" }}
            onClick={() => navigate(crumb.path!)}
          >
            {crumb.label}
          </Link>
        );
      })}
    </Breadcrumbs>
  );
}
