/**
 * App shell layout with sidebar navigation and auth-aware header.
 *
 * Shows:
 * - Branded sidebar with grouped nav links
 * - Top bar with user info + login/logout
 * - Main content area via <Outlet />
 */

import React from "react";
import { useNavigate, useLocation, Outlet } from "react-router-dom";
import RouteErrorBoundary from "./RouteErrorBoundary";
import {
  AppBar,
  Avatar,
  Box,
  Button,
  Chip,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import DashboardIcon from "@mui/icons-material/Dashboard";
import RateReviewIcon from "@mui/icons-material/RateReview";
import QuizIcon from "@mui/icons-material/Quiz";
import TimerIcon from "@mui/icons-material/Timer";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import InsightsIcon from "@mui/icons-material/Insights";
import PaymentIcon from "@mui/icons-material/Payment";
import GavelIcon from "@mui/icons-material/Gavel";
import GroupsIcon from "@mui/icons-material/Groups";
import DescriptionIcon from "@mui/icons-material/Description";
import LoginIcon from "@mui/icons-material/Login";
import LogoutIcon from "@mui/icons-material/Logout";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import { useAuth } from "../hooks/useAuth";

const DRAWER_WIDTH = 256;

// ---------------------------------------------------------------------------
// Navigation structure — grouped for visual hierarchy
// ---------------------------------------------------------------------------

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  badge?: string;
}

interface NavGroup {
  heading: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    heading: "Practice",
    items: [
      { path: "/", label: "Dashboard", icon: <DashboardIcon /> },
      { path: "/evaluate", label: "New Evaluation", icon: <RateReviewIcon /> },
      { path: "/mock", label: "Mock Interview", icon: <TimerIcon /> },
      { path: "/generator", label: "AI Generator", icon: <AutoAwesomeIcon /> },
    ],
  },
  {
    heading: "Library",
    items: [
      { path: "/questions", label: "Question Bank", icon: <QuizIcon /> },
      { path: "/templates", label: "Templates", icon: <DescriptionIcon /> },
    ],
  },
  {
    heading: "Growth",
    items: [
      { path: "/coaching", label: "Coaching", icon: <GroupsIcon /> },
      { path: "/analytics", label: "Analytics", icon: <InsightsIcon /> },
    ],
  },
  {
    heading: "Account",
    items: [{ path: "/pricing", label: "Pricing", icon: <PaymentIcon /> }],
  },
];

export default function Layout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuth();

  // Build nav groups — moderators get an extra link
  const navGroups = React.useMemo(() => {
    const groups = NAV_GROUPS.map((g) => ({ ...g, items: [...g.items] }));
    if (user?.is_moderator) {
      const libraryGroup = groups.find((g) => g.heading === "Library");
      if (libraryGroup) {
        libraryGroup.items.push({
          path: "/moderation",
          label: "Moderation",
          icon: <GavelIcon />,
        });
      }
    }
    return groups;
  }, [user?.is_moderator]);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const isActive = (path: string) =>
    path === "/" ? location.pathname === "/" : location.pathname.startsWith(path);

  const drawer = (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Brand mark */}
      <Box sx={{ px: 2.5, py: 2.5 }}>
        <Stack
          direction="row"
          alignItems="center"
          spacing={1.5}
          sx={{ cursor: "pointer" }}
          onClick={() => navigate("/")}
        >
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: "10px",
              bgcolor: "primary.main",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <SmartToyIcon sx={{ color: "white", fontSize: 20 }} />
          </Box>
          <Box>
            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 800,
                fontSize: "1rem",
                color: "text.primary",
                lineHeight: 1.2,
                letterSpacing: "-0.02em",
              }}
            >
              Career Foundry
            </Typography>
            <Typography
              variant="caption"
              sx={{ color: "text.secondary", fontSize: "0.7rem" }}
            >
              AI Interview Coach
            </Typography>
          </Box>
        </Stack>
      </Box>

      <Divider sx={{ mx: 2 }} />

      {/* Navigation groups */}
      <Box sx={{ flex: 1, overflow: "auto", py: 1 }}>
        {navGroups.map((group) => (
          <List
            key={group.heading}
            dense
            subheader={
              <ListSubheader
                disableSticky
                sx={{
                  fontSize: "0.68rem",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: "text.secondary",
                  lineHeight: "32px",
                  px: 2.5,
                  mt: 0.5,
                }}
              >
                {group.heading}
              </ListSubheader>
            }
          >
            {group.items.map((item) => {
              const active = isActive(item.path);
              return (
                <Tooltip
                  key={item.path}
                  title={item.label}
                  placement="right"
                  disableHoverListener={!isMobile}
                  arrow
                >
                  <ListItemButton
                    selected={active}
                    onClick={() => {
                      navigate(item.path);
                      if (isMobile) setMobileOpen(false);
                    }}
                    sx={{
                      my: 0.25,
                      py: 0.75,
                      ...(active && {
                        bgcolor: "primary.main",
                        color: "primary.contrastText",
                        "&:hover": {
                          bgcolor: "primary.dark",
                        },
                        "& .MuiListItemIcon-root": {
                          color: "primary.contrastText",
                        },
                      }),
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: 36,
                        color: active ? "inherit" : "text.secondary",
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{
                        fontSize: "0.85rem",
                        fontWeight: active ? 600 : 500,
                      }}
                    />
                    {item.badge && (
                      <Chip
                        label={item.badge}
                        size="small"
                        color="secondary"
                        sx={{ height: 20, fontSize: 10, fontWeight: 700 }}
                      />
                    )}
                  </ListItemButton>
                </Tooltip>
              );
            })}
          </List>
        ))}
      </Box>

      {/* Bottom section — user context */}
      {isAuthenticated && user && (
        <>
          <Divider sx={{ mx: 2 }} />
          <Box sx={{ p: 2 }}>
            <Stack direction="row" alignItems="center" spacing={1.5}>
              <Avatar
                src={user.avatar_url || undefined}
                sx={{
                  width: 32,
                  height: 32,
                  bgcolor: "secondary.main",
                  fontSize: 13,
                  fontWeight: 700,
                }}
              >
                {(user.display_name || user.email || "U")
                  .charAt(0)
                  .toUpperCase()}
              </Avatar>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  variant="body2"
                  fontWeight={600}
                  noWrap
                  sx={{ fontSize: "0.8rem" }}
                >
                  {user.display_name || user.email}
                </Typography>
                {user.plan_tier && (
                  <Chip
                    label={user.plan_tier === "pro" ? "Pro" : "Free"}
                    size="small"
                    color={user.plan_tier === "pro" ? "secondary" : "default"}
                    variant="outlined"
                    sx={{ height: 18, fontSize: 10, mt: 0.25 }}
                  />
                )}
              </Box>
            </Stack>
          </Box>
        </>
      )}
    </Box>
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      {/* Top bar — clean, minimal */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
          bgcolor: "background.paper",
          color: "text.primary",
          borderBottom: 1,
          borderColor: "divider",
        }}
      >
        <Toolbar sx={{ minHeight: { xs: 56, sm: 64 } }}>
          {isMobile && (
            <IconButton
              edge="start"
              onClick={() => setMobileOpen(!mobileOpen)}
              sx={{ mr: 1.5 }}
            >
              <MenuIcon />
            </IconButton>
          )}

          {/* Mobile brand */}
          {isMobile && (
            <Typography
              variant="subtitle1"
              fontWeight={700}
              sx={{ flexGrow: 1, letterSpacing: "-0.01em" }}
            >
              Career Foundry
            </Typography>
          )}

          {!isMobile && <Box sx={{ flexGrow: 1 }} />}

          {/* Auth section */}
          {isAuthenticated ? (
            <Button
              size="small"
              startIcon={<LogoutIcon />}
              onClick={handleLogout}
              sx={{
                color: "text.secondary",
                "&:hover": { color: "text.primary" },
              }}
            >
              Logout
            </Button>
          ) : (
            <Button
              variant="contained"
              size="small"
              startIcon={<LoginIcon />}
              onClick={() => navigate("/login")}
            >
              Sign In
            </Button>
          )}
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Box
        component="nav"
        sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
      >
        {isMobile ? (
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={() => setMobileOpen(false)}
            ModalProps={{ keepMounted: true }}
            sx={{
              "& .MuiDrawer-paper": {
                width: DRAWER_WIDTH,
                bgcolor: "background.paper",
              },
            }}
          >
            {drawer}
          </Drawer>
        ) : (
          <Drawer
            variant="permanent"
            sx={{
              "& .MuiDrawer-paper": {
                width: DRAWER_WIDTH,
                boxSizing: "border-box",
                bgcolor: "background.paper",
              },
            }}
            open
          >
            {drawer}
          </Drawer>
        )}
      </Box>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, sm: 3 },
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          bgcolor: "background.default",
          minHeight: "100vh",
        }}
      >
        <Toolbar sx={{ minHeight: { xs: 56, sm: 64 } }} />
        <RouteErrorBoundary resetKey={location.pathname}>
          <Outlet />
        </RouteErrorBoundary>
      </Box>
    </Box>
  );
}
