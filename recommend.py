"""
Book Recommendation module (rule-based).

Referenced in the report as: "a book recommendation module created by a
rule-based system that will utilize their past borrowing records to
suggest pertinent books."

Two rules are implemented:
  1. same_category()      - given a book, suggest other AVAILABLE books
                             in the same category (used by the chatbot
                             when the requested book is unavailable - FR9).
  2. for_member()          - given a member, look at their most-borrowed
                             category and suggest available books from it
                             that they have not already borrowed.
"""

from db import query_all


def same_category(category_id, exclude_book_id=None, limit=3):
    """Rule 1: recommend available books from the same category."""
    if not category_id:
        return []

    sql = """
        SELECT Book_ID, ISBN, Title, Author, Status
        FROM Book
        WHERE Category_ID = %s AND Status = 'Available'
    """
    params = [category_id]

    if exclude_book_id:
        sql += " AND Book_ID != %s"
        params.append(exclude_book_id)

    sql += " LIMIT %s"
    params.append(limit)

    return query_all(sql, params)


def for_member(member_id, limit=5):
    """Rule 2: recommend books based on the member's borrowing history."""
    favourite_category = query_all(
        """
        SELECT b.Category_ID, COUNT(*) AS cnt
        FROM Borrowing br
        JOIN Book b ON br.Book_ID = b.Book_ID
        WHERE br.Member_ID = %s AND b.Category_ID IS NOT NULL
        GROUP BY b.Category_ID
        ORDER BY cnt DESC
        LIMIT 1
        """,
        (member_id,),
    )

    if not favourite_category:
        # No borrowing history yet -> just suggest popular available books
        return query_all(
            """
            SELECT b.Book_ID, b.ISBN, b.Title, b.Author, c.Category_Name
            FROM Borrowing br
            JOIN Book b ON br.Book_ID = b.Book_ID
            LEFT JOIN Category c ON b.Category_ID = c.Category_ID
            WHERE b.Status = 'Available'
            GROUP BY b.Book_ID
            ORDER BY COUNT(*) DESC
            LIMIT %s
            """,
            (limit,),
        )

    category_id = favourite_category[0]["Category_ID"]

    return query_all(
        """
        SELECT b.Book_ID, b.ISBN, b.Title, b.Author, c.Category_Name
        FROM Book b
        LEFT JOIN Category c ON b.Category_ID = c.Category_ID
        WHERE b.Category_ID = %s
          AND b.Status = 'Available'
          AND b.Book_ID NOT IN (
              SELECT Book_ID FROM Borrowing WHERE Member_ID = %s
          )
        LIMIT %s
        """,
        (category_id, member_id, limit),
    )
