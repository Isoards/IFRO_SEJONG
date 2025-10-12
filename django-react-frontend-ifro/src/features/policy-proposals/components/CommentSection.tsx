import React, { useState, useEffect } from "react";
import {
  ProposalComment,
  CreateCommentRequest,
  UpdateCommentRequest,
} from "../../../shared/types/global.types";
import {
  getProposalComments,
  createProposalComment,
  updateProposalComment,
  deleteProposalComment,
  getCommentReplies,
} from "../../../shared/services/proposals";
import { getCurrentUser } from "../../../shared/services/user";

interface CommentSectionProps {
  proposalId: number;
}

interface CommentItemProps {
  comment: ProposalComment;
  proposalId: number;
  currentUserId?: number;
  onCommentUpdate: () => void;
  onCommentDelete: () => void;
}

const CommentItem: React.FC<CommentItemProps> = ({
  comment,
  proposalId,
  currentUserId,
  onCommentUpdate,
  onCommentDelete,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const [showReplies, setShowReplies] = useState(false);
  const [replies, setReplies] = useState<ProposalComment[]>([]);
  const [isLoadingReplies, setIsLoadingReplies] = useState(false);
  const [replyContent, setReplyContent] = useState("");
  const [isSubmittingReply, setIsSubmittingReply] = useState(false);

  const isAuthor = currentUserId === comment.author_id;
  const canEdit = isAuthor && !comment.is_deleted;

  const handleEdit = () => {
    setIsEditing(true);
    setEditContent(comment.content);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditContent(comment.content);
  };

  const handleSaveEdit = async () => {
    try {
      await updateProposalComment(proposalId, comment.id, {
        content: editContent,
      });
      setIsEditing(false);
      onCommentUpdate();
    } catch (error) {
      console.error("댓글 수정 실패:", error);
      alert("댓글 수정에 실패했습니다.");
    }
  };

  const handleDelete = async () => {
    if (window.confirm("댓글을 삭제하시겠습니까?")) {
      try {
        await deleteProposalComment(proposalId, comment.id);
        onCommentDelete();
      } catch (error) {
        console.error("댓글 삭제 실패:", error);
        alert("댓글 삭제에 실패했습니다.");
      }
    }
  };

  const handleToggleReplies = async () => {
    if (!showReplies && comment.reply_count > 0) {
      setIsLoadingReplies(true);
      try {
        const repliesData = await getCommentReplies(proposalId, comment.id);
        setReplies(repliesData);
      } catch (error) {
        console.error("대댓글 로딩 실패:", error);
      } finally {
        setIsLoadingReplies(false);
      }
    }
    setShowReplies(!showReplies);
  };

  const handleSubmitReply = async () => {
    if (!replyContent.trim()) return;

    setIsSubmittingReply(true);
    try {
      await createProposalComment(proposalId, {
        content: replyContent,
        parent_comment_id: comment.id,
      });
      setReplyContent("");
      onCommentUpdate();
      // 대댓글 목록 새로고침
      if (showReplies) {
        const repliesData = await getCommentReplies(proposalId, comment.id);
        setReplies(repliesData);
      }
    } catch (error) {
      console.error("대댓글 작성 실패:", error);
      alert("대댓글 작성에 실패했습니다.");
    } finally {
      setIsSubmittingReply(false);
    }
  };

  if (comment.is_deleted) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-gray-500 italic">
        삭제된 댓글입니다.
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      {/* 댓글 헤더 */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="font-medium text-gray-900">{comment.author}</span>
          <span className="text-sm text-gray-500">
            {new Date(comment.created_at).toLocaleString()}
          </span>
        </div>
        {canEdit && (
          <div className="flex space-x-2">
            <button
              onClick={handleEdit}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              수정
            </button>
            <button
              onClick={handleDelete}
              className="text-sm text-red-600 hover:text-red-800"
            >
              삭제
            </button>
          </div>
        )}
      </div>

      {/* 댓글 내용 */}
      {isEditing ? (
        <div className="space-y-2">
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md resize-none"
            rows={3}
          />
          <div className="flex space-x-2">
            <button
              onClick={handleSaveEdit}
              className="px-3 py-1 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
            >
              저장
            </button>
            <button
              onClick={handleCancelEdit}
              className="px-3 py-1 bg-gray-500 text-white rounded-md text-sm hover:bg-gray-600"
            >
              취소
            </button>
          </div>
        </div>
      ) : (
        <div className="text-gray-800 whitespace-pre-wrap">{comment.content}</div>
      )}

      {/* 대댓글 토글 및 작성 */}
      <div className="mt-3 pt-3 border-t border-gray-100">
        <button
          onClick={handleToggleReplies}
          className="text-sm text-blue-600 hover:text-blue-800 mb-2"
        >
          {showReplies ? "답글 숨기기" : `답글 보기 (${comment.reply_count})`}
        </button>

        {showReplies && (
          <div className="mt-2 space-y-2">
            {/* 대댓글 목록 */}
            {isLoadingReplies ? (
              <div className="text-sm text-gray-500">답글을 불러오는 중...</div>
            ) : (
              replies.map((reply) => (
                <div key={reply.id} className="ml-4 bg-gray-50 p-3 rounded">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sm text-gray-900">
                      {reply.author}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(reply.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="text-sm text-gray-800">{reply.content}</div>
                </div>
              ))
            )}

            {/* 대댓글 작성 폼 */}
            <div className="ml-4 mt-2">
              <textarea
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                placeholder="답글을 작성하세요..."
                className="w-full p-2 border border-gray-300 rounded-md resize-none text-sm"
                rows={2}
              />
              <div className="mt-1 flex justify-end">
                <button
                  onClick={handleSubmitReply}
                  disabled={!replyContent.trim() || isSubmittingReply}
                  className="px-3 py-1 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {isSubmittingReply ? "작성 중..." : "답글 작성"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const CommentSection: React.FC<CommentSectionProps> = ({ proposalId }) => {
  const [comments, setComments] = useState<ProposalComment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [newComment, setNewComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    loadComments();
    loadCurrentUser();
  }, [proposalId, page]);

  const loadCurrentUser = async () => {
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
    } catch (error) {
      console.error("사용자 정보 로딩 실패:", error);
    }
  };

  const loadComments = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getProposalComments(proposalId, page, 20);
      setComments(response.comments);
      setTotalPages(response.total_pages);
    } catch (error) {
      console.error("댓글 로딩 실패:", error);
      setError("댓글을 불러올 수 없습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitComment = async () => {
    if (!newComment.trim()) return;

    setIsSubmitting(true);
    try {
      await createProposalComment(proposalId, {
        content: newComment,
      });
      setNewComment("");
      loadComments(); // 댓글 목록 새로고침
    } catch (error) {
      console.error("댓글 작성 실패:", error);
      alert("댓글 작성에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCommentUpdate = () => {
    loadComments();
  };

  const handleCommentDelete = () => {
    loadComments();
  };

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">댓글</h3>

      {/* 댓글 작성 폼 */}
      {currentUser && (
        <div className="mb-6">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="댓글을 작성하세요..."
            className="w-full p-3 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={3}
          />
          <div className="mt-2 flex justify-end">
            <button
              onClick={handleSubmitComment}
              disabled={!newComment.trim() || isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              {isSubmitting ? "작성 중..." : "댓글 작성"}
            </button>
          </div>
        </div>
      )}

      {/* 댓글 목록 */}
      {error ? (
        <div className="text-red-600 text-center py-4">{error}</div>
      ) : comments.length === 0 ? (
        <div className="text-gray-500 text-center py-8">
          아직 댓글이 없습니다. 첫 번째 댓글을 작성해보세요!
        </div>
      ) : (
        <div className="space-y-4">
          {comments.map((comment) => (
            <CommentItem
              key={comment.id}
              comment={comment}
              proposalId={proposalId}
              currentUserId={currentUser?.id}
              onCommentUpdate={handleCommentUpdate}
              onCommentDelete={handleCommentDelete}
            />
          ))}
        </div>
      )}

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="mt-6 flex justify-center space-x-2">
          <button
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
          >
            이전
          </button>
          <span className="px-3 py-1 text-sm text-gray-600">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={page === totalPages}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
          >
            다음
          </button>
        </div>
      )}
    </div>
  );
};

export default CommentSection;



