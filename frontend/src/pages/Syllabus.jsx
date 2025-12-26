import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Menu,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Paper,
  Collapse,
} from "@mui/material";
import {
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  MoreVert as MoreVertIcon,
} from "@mui/icons-material";
import api from "../services/api";

export default function Syllabus() {
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState("add"); // 'add', 'edit', 'addChild'
  const [currentTag, setCurrentTag] = useState(null);
  const [parentTagId, setParentTagId] = useState(null);
  const [formData, setFormData] = useState({ name: "", content: "" });
  const [contextMenu, setContextMenu] = useState(null);
  const [expandedTags, setExpandedTags] = useState(new Set());
  const [showContent, setShowContent] = useState(true); // 控制是否显示标签备注

  useEffect(() => {
    // 从token中获取真实的user_type，确保一致性
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    try {
      // 解码 token 获取真实的 user_type
      const payload = JSON.parse(atob(token.split(".")[1]));
      const actualUserType = payload.user_type;

      // 如果token中的user_type不是teacher，拒绝访问
      if (actualUserType !== "teacher") {
        alert("只有教师才能访问教学大纲。当前用户类型：" + actualUserType);
        window.location.href = "/";
        return;
      }

      // 更新localStorage中的userType，确保一致性
      localStorage.setItem("userType", actualUserType);

      fetchTags();
    } catch (e) {
      console.error("Error decoding token:", e);
      alert("Token解析失败，请重新登录");
      localStorage.clear();
      window.location.href = "/login";
    }
  }, []);

  const fetchTags = async () => {
    try {
      const response = await api.get("/syllabus/tags");
      setTags(response.data);
    } catch (error) {
      console.error("Error fetching tags:", error);
      if (error.response) {
        console.error("Error details:", error.response.data);
        // 如果是权限错误，提示用户重新登录
        if (error.response.status === 403) {
          alert(
            `权限错误: ${error.response.data.detail}\n请确保使用教师身份登录。如果问题持续，请清除浏览器缓存并重新登录。`
          );
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAddRootTag = () => {
    setDialogType("add");
    setCurrentTag(null);
    setParentTagId(null);
    setFormData({ name: "", content: "" });
    setOpenDialog(true);
  };

  const handleEditTag = (tag) => {
    setDialogType("edit");
    setCurrentTag(tag);
    setParentTagId(null);
    setFormData({ name: tag.name, content: tag.content || "" });
    setOpenDialog(true);
    setContextMenu(null);
  };

  const handleAddChildTag = (parentTag) => {
    setDialogType("addChild");
    setCurrentTag(null);
    setParentTagId(parentTag.id);
    setFormData({ name: "", content: "" });
    setOpenDialog(true);
    setContextMenu(null);
  };

  const handleDeleteTag = async (tag) => {
    if (window.confirm(`确定要删除标签"${tag.name}"及其所有子标签吗？`)) {
      try {
        await api.delete(`/syllabus/tags/${tag.id}`);
        fetchTags();
        // 从展开列表中移除
        const newExpanded = new Set(expandedTags);
        newExpanded.delete(tag.id);
        setExpandedTags(newExpanded);
      } catch (error) {
        console.error("Error deleting tag:", error);
        alert("删除失败");
      }
    }
    setContextMenu(null);
  };

  const handleDialogSubmit = async () => {
    if (!formData.name.trim()) {
      alert("请输入标签名称");
      return;
    }

    try {
      if (dialogType === "add" || dialogType === "addChild") {
        await api.post("/syllabus/tags", {
          name: formData.name,
          content: formData.content,
          parent_id: dialogType === "addChild" ? parentTagId : null,
          order: 0,
        });
      } else if (dialogType === "edit") {
        await api.put(`/syllabus/tags/${currentTag.id}`, {
          name: formData.name,
          content: formData.content,
        });
      }
      setOpenDialog(false);
      fetchTags();
      // 如果是添加子标签，展开父标签
      if (dialogType === "addChild") {
        const newExpanded = new Set(expandedTags);
        newExpanded.add(parentTagId);
        setExpandedTags(newExpanded);
      }
    } catch (error) {
      console.error("Error saving tag:", error);
      alert("保存失败");
    }
  };

  const handleContextMenu = (event, tag) => {
    event.preventDefault();
    setContextMenu({
      mouseX: event.clientX - 2,
      mouseY: event.clientY - 4,
      tag: tag,
    });
  };

  const handleCloseContextMenu = () => {
    setContextMenu(null);
  };

  const toggleExpand = (tagId) => {
    const newExpanded = new Set(expandedTags);
    if (newExpanded.has(tagId)) {
      newExpanded.delete(tagId);
    } else {
      newExpanded.add(tagId);
    }
    setExpandedTags(newExpanded);
  };

  const renderTag = (tag, level = 0) => {
    const hasChildren = tag.children && tag.children.length > 0;
    const isExpanded = expandedTags.has(tag.id);

    return (
      <React.Fragment key={tag.id}>
        <ListItem
          sx={{
            pl: 2 + level * 3,
            py: 1,
            "&:hover": {
              backgroundColor: "action.hover",
            },
          }}
          onContextMenu={(e) => handleContextMenu(e, tag)}
        >
          {hasChildren && (
            <IconButton
              size="small"
              onClick={() => toggleExpand(tag.id)}
              sx={{ mr: 1 }}
            >
              {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          )}
          {!hasChildren && <Box sx={{ width: 40 }} />}
          <ListItemText
            primary={
              <Typography variant="body1" fontWeight="medium">
                {tag.name}
              </Typography>
            }
            secondary={
              showContent &&
              tag.content && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mt: 0.5 }}
                >
                  {tag.content}
                </Typography>
              )
            }
          />
          <IconButton size="small" onClick={(e) => handleContextMenu(e, tag)}>
            <MoreVertIcon />
          </IconButton>
        </ListItem>
        {hasChildren && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {tag.children.map((child) => renderTag(child, level + 1))}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    );
  };

  if (loading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          教学大纲
        </Typography>
        <Typography>加载中...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Typography variant="h4">教学大纲</Typography>
        <Box sx={{ display: "flex", gap: 2 }}>
          <Button
            variant="outlined"
            onClick={() => setShowContent(!showContent)}
          >
            {showContent ? "隐藏标签备注" : "显示标签备注"}
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAddRootTag}
          >
            添加根标签
          </Button>
        </Box>
      </Box>

      <Paper>
        {tags.length === 0 ? (
          <Box sx={{ p: 3, textAlign: "center" }}>
            <Typography color="text.secondary">
              暂无标签，点击"添加根标签"开始创建
            </Typography>
          </Box>
        ) : (
          <List>{tags.map((tag) => renderTag(tag))}</List>
        )}
      </Paper>

      {/* 添加/编辑对话框 */}
      <Dialog
        open={openDialog}
        onClose={() => setOpenDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {dialogType === "add"
            ? "添加根标签"
            : dialogType === "addChild"
            ? "添加子标签"
            : "编辑标签"}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="标签名称"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="标签说明"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            value={formData.content}
            onChange={(e) =>
              setFormData({ ...formData, content: e.target.value })
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>取消</Button>
          <Button onClick={handleDialogSubmit} variant="contained">
            确定
          </Button>
        </DialogActions>
      </Dialog>

      {/* 右键菜单 */}
      <Menu
        open={contextMenu !== null}
        onClose={handleCloseContextMenu}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
      >
        {contextMenu && (
          <>
            <MenuItem onClick={() => handleEditTag(contextMenu.tag)}>
              修改
            </MenuItem>
            <MenuItem onClick={() => handleAddChildTag(contextMenu.tag)}>
              添加子标签
            </MenuItem>
            <MenuItem onClick={() => handleDeleteTag(contextMenu.tag)}>
              删除
            </MenuItem>
          </>
        )}
      </Menu>
    </Box>
  );
}
