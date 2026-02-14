/**
 * App shell layout with sidebar navigation and auth-aware header.
 *
 * Shows:
 * - Sidebar with nav links to all features
 * - Top bar with user info + login/logout button
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
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
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
import { useAuth } from "../hooks/useAuth";

const DRAWER_WIDTH = 240;

const BASE_NAV_ITEMS = [
  { path: "/", label: "Dashboard", icon: <DashboardIcon /> },
  { path: "/evaluate", label: "New Evaluation", icon: <RateReviewIcon /> },
  { path: "/mock", label: "Mock Interview", icon: <TimerIcon /> },
  { path: "/generator", label: "AI Generator", icon: <AutoAwesomeIcon /> },
  { path: "/questions", label: "Question Bank", icon: <QuizIcon /> },
  { path: "/templates", label: "Templates", icon: <DescriptionIcon /> },
  { path: "/coaching", label: "Coaching", icon: <GroupsIcon /> },
  { path: "/analytics", label: "Analytics", icon: <InsightsIcon /> },
  { path: "/pricing", label: "Pricing", icon: <PaymentIcon /> },
];

export default function Layout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuth();

  // Build nav items — moderators get an extra link
  const navItems = React.useMemo(() => {
    const items = [...BASE_NAV_ITEMS];
    if (user?.is_moderator) {
      // Insert moderation link after Question Bank
      const qbIndex = items.findIndex((i) => i.path === "/questions");
      items.splice(qbIndex + 1, 0, {
        path: "/moderation",
        label: "Moderation",
        icon: <GavelIcon />,
      });
    }
    return items;
  }, [user?.is_moderator]);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap sx={{ fontWeight: 700 }}>
          BIAE
        </Typography>
      </Toolbar>
      <List>
        {navItems.map((item) => (
          <ListItemButton
            key={item.path}
            selected={location.pathname === item.path}
            onClick={() => {
              navigate(item.path);
              if (isMobile) setMobileOpen(false);
            }}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
        }}
      >
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              edge="start"
              onClick={() => setMobileOpen(!mobileOpen)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Typography
            variant="h6"
            noWrap
            sx={{
              flexGrow: 1,
              fontSize: { xs: "1rem", sm: "1.25rem" },
            }}
          >
            <Box component="span" sx={{ display: { xs: "none", sm: "inline" } }}>
              Behavioral Interview Answer Evaluator
            </Box>
            <Box component="span" sx={{ display: { xs: "inline", sm: "none" } }}>
              BIAE
            </Box>
          </Typography>

          {/* Auth section */}
          {isAuthenticated ? (
            <Stack direction="row" alignItems="center" spacing={1.5}>
              <Avatar
                src={user?.avatar_url || undefined}
                sx={{
                  width: 32,
                  height: 32,
                  bgcolor: "secondary.main",
                  fontSize: 14,
                  fontWeight: 600,
                }}
              >
                {(user?.display_name || user?.email || "U")
                  .charAt(0)
                  .toUpperCase()}
              </Avatar>
              <Typography
                variant="body2"
                sx={{ display: { xs: "none", sm: "block" } }}
              >
                {user?.display_name || user?.email}
              </Typography>
              <Button
                color="inherit"
                size="small"
                startIcon={<LogoutIcon />}
                onClick={handleLogout}
                sx={{ ml: 1 }}
              >
                Logout
              </Button>
            </Stack>
          ) : (
            <Button
              color="inherit"
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
            sx={{ "& .MuiDrawer-paper": { width: DRAWER_WIDTH } }}
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
        }}
      >
        <Toolbar /> {/* Spacer for fixed AppBar */}
        <RouteErrorBoundary resetKey={location.pathname}>
          <Outlet />
        </RouteErrorBoundary>
      </Box>
    </Box>
  );
}
