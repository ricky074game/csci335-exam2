# 03 - Binary Heaps and Priority Queues (Textbook 6.1-6.4, "Heaps" slides, HW6)

> **Priority: high.** Heaps are Exam 2's "data-structure implementation" topic from Ch. 6. Expect (a) at least one **trace** (insert / deleteMin /
> buildHeap on a short array, with **index 0 shown** the way HW6 Q2 asks), (b) a **proof or complexity** question (why buildHeap is O(n), why insert is O(1)
> on average, where the max lives), and (c) heaps used as a tool inside a "design a solution and analyze it" question
> (`priority_queue`, k-th largest, merge k lists, selection with 6A/6B). HW6 questions 6.1-6.8, 6.10, 6.18 and Q2/Q4 are all fair game; worked answers are in section 12.
> The companion note `06-heapsort-introsort.md` covers Ch. 7 heapsort, which uses a **different array layout**.

**Conventions (textbook-exact: if you use a different variant, it is graded wrong):**

| Item | Rule |
|---|---|
| Kind | **Min**-heap unless told "max-heap" (the book's `deleteMin`, `findMin`). |
| Array | `array[0]` is **not** part of the heap; the root is `array[1]`; `currentSize` = number of elements. |
| Navigation | left child of `i` is `2i`, right child `2i+1`, parent `i/2` (integer division). |
| Depth D | occupies indices `2^D` .. `2^(D+1)-1` (depth 3 = indices 8-15). |
| insert | hole at index `currentSize+1`; copy of x in `array[0]`; slide parents down while `x < parent` (strict, **ties stop**). |
| deleteMin | last element moved into the hole at the root, `currentSize` decreases, then `percolateDown(1)`; the **smaller child** moves up, **ties between the children go LEFT**; stop when `child < tmp` is false (ties stop). |
| buildHeap | `for (i = currentSize/2; i > 0; --i) percolateDown(i);` |
| Index 0 in a trace | holds the value being moved (`tmp`); on the exam show it after every step (HW6 Q2). `_` = the hole. |

---

## 1. Priority queue (ADT) versus heap (data structure) - textbook 6.1, 6.2, slides "Priority Queues / ADTs and Data Structures"

A **priority queue** is an *abstract data type*: elements with priorities, and two required operations: **insert** an element, and **deleteMin**
(remove and return the element with the highest priority; for the book, "highest priority" = smallest key). A **binary heap** is one *data structure*
that implements it. Same relationship as `list` (ADT) versus linked list or array (implementations). The slides stress that they are
"conceptually distinct", even though people say "heap" when they mean "priority queue".

What the ADT does **not** give you: finding an arbitrary element, changing the priority of an element, merging two queues. A heap is good at the two required
operations and bad at those (no way to find an element without scanning all of them; this is why graph algorithms that lower priorities need extra machinery).

### Simple implementations (6.2) and why they lose

| Implementation | insert | deleteMin | findMin | Comment |
|---|---|---|---|---|
| Unsorted list / vector (insert at front or back) | O(1) | O(N) (scan for the min) | O(N) | book: "probably the better of the two" because deleteMins never outnumber inserts |
| Always-sorted list | O(N) | O(1) | O(1) | insert has to find the place |
| Binary search tree | O(log N) **average** | O(log N) average | O(log N) | overkill: supports many unneeded operations; bad deletions of only the min skew the tree, but only by a constant factor; a **balanced** tree (AVL) makes it worst case |
| **Binary heap** | **O(log N) worst, O(1) average** | **O(log N)** worst and average | **O(1)** | no links, one array; buildHeap of N items in O(N) |

- Heap versus balanced BST: both O(log N) worst-case for insert and deleteMin, but the heap has a **smaller constant**, uses one flat array (cache friendly, few
  allocations), inserts in O(1) on average, and builds in O(N) (a BST needs O(N log N)). A BST can also find any element and traverse in sorted order; a heap cannot.
- Textbook 6.1 (HW6): *"Can both insert and findMin be done in constant time?"* **Yes**, if you give up cheap deleteMin: keep an unsorted list plus a variable holding the
  current minimum (insert compares with it). It cannot be combined with an efficient deleteMin: after deleting the min you must rescan to find the next min.
  In a heap, findMin is O(1) worst case but insert is O(1) only **on average** (worst case O(log N)).

**Check yourself**
1. Name two implementations of the priority queue ADT and give insert/deleteMin costs for each. 2. Why isn't a hash table a good priority queue? 3. Which op does the heap do in O(1) worst case?

<details><summary>Answer</summary>

1. Sorted array/list: insert O(N), deleteMin O(1). Unsorted list: insert O(1), deleteMin O(N). (Balanced BST: both O(log N); heap: O(log N) worst / O(1) average for insert, O(log N) for deleteMin.)
2. A hash table has no order, so finding the minimum means scanning all N entries: O(N) per deleteMin. 3. findMin (read `array[1]`).
</details>

---

## 2. What a heap is: structure property + heap-order property (6.3.1, 6.3.2)

Start with a picture. This is Figure 6.5 (left) of the book, a valid min-heap of 10 elements:

```
                13                      array (index 0 unused):
             /      \                   index:  1  2  3  4  5  6  7  8  9  10
          21          16                value: 13 21 16 24 31 19 68 65 26 32
        /    \       /   \
      24      31   19     68            node 24 (index 4): children indices 8, 9  -> 65, 26
     /  \    /                          node 31 (index 5): children indices 10, 11 -> 32, (none)
   65   26  32                          node 16 (index 3): children indices 6, 7  -> 19, 68
```

A binary heap has **two** properties, and every operation must restore **both** before it ends:

1. **Structure property**: it is a **complete binary tree**. Every level is full except possibly the last, which is filled **left to right** with no gaps.
   Consequences: a complete tree of height h has between 2^h and 2^(h+1)-1 nodes, so the height is **floor(log2 N) = O(log N)**.
2. **Heap-order property** (min-heap): for every node X other than the root, **key(parent) <= key(X)** (equal keys are allowed). So every node is <= all of its
   **descendants**, and the minimum is always at the root (findMin is O(1)).

Not guaranteed: any ordering between a node and nodes that are *not its descendants*. In the picture, 68 (depth 2) is bigger than 26 (depth 3); 31 and 24 are siblings with no required order.
**A heap is not a sorted array**: reading the array left to right does not give sorted order, and the k-th array slot is not the k-th smallest (slides: "position does not indicate order", and
also not order of insertion).

Use the engine's checker to test claims. Left tree of Fig 6.5, then the right one (where 65 was replaced by 6):

```
$ python tools/study.py heap check 13,21,16,24,31,19,68,65,26,32
valid min-heap
```

```
$ python tools/study.py heap check 13,21,16,24,31,19,68,6,26,32
NOT a min-heap:
  index 8 (6) < its parent index 4 (24)
```


(The violation: 6 is at index 8, its parent is index 4 holding 24, and 6 < 24.)

### Facts you must be able to compute (N elements, array indices 1..N)

| Question | Formula | Example N = 10 |
|---|---|---|
| parent of i | `i/2` (floor) | parent of 9 is 4 |
| children of i | `2i`, `2i+1` (only if <= N) | children of 4: 8, 9 |
| depth of node i | `floor(log2 i)` | node 9: depth 3 |
| indices at depth D | `2^D` .. `2^(D+1)-1` (last level may stop at N) | depth 3: 8..10 |
| height of the heap | `floor(log2 N)` | 3 |
| last internal node | `floor(N/2)` | 5 |
| leaves | indices `floor(N/2)+1` .. `N`; there are **ceil(N/2)** of them | 6..10: 5 leaves |
| node with exactly one child | `2i = N` (only when N is even) | node 5 has only a left child (index 10) |

If N is **even**, node N/2 has exactly one child (a left child). This is the special case every percolateDown must handle (see section 5).
Nodes at height h (distance to the deepest leaf below) number about N/2^(h+1); the number of nodes with height >= k is `floor(N/2^k)` (used in the buildHeap proof).

### Why an array (slides "Array Implementation / Benefits")

- Complete tree => no gaps => store level by level; no pointers (`2i`, `2i+1`, `i/2` are cheap shifts).
- Benefits (slides): fewer memory allocations, better cache behavior, **O(1)** to add the new element at the end (this is only the placement step; fixing order is separate).
- Textbook caveat: you need a capacity estimate (resize by doubling when full, as in Fig 6.8 line 6-7).
- *Access by position* is O(1) but **useless**: the k-th element of the array is not the k-th highest priority and position says nothing about insertion order, so "access" is not considered a heap operation.
- Index 0 is left empty so the arithmetic is `2i`, `2i+1`, `i/2`; the book uses cell 0 as scratch space (the sentinel in `insert`, `tmp` in HW6's trace convention).
  Other implementations start at 0 (children `2i+1`, `2i+2`): that is the heapsort layout, note 06.

**Check yourself**
1. N = 1000. Height? Number of leaves? Parent and children of index 300? Depth of index 700? 2. Is `[2, 5, 3, 9, 4, 8, 7]` a min-heap? 3. Why is `[1,2,3,...]` sorted ascending always a valid min-heap, but not conversely?

<details><summary>Answer</summary>

1. height floor(log2 1000) = 9 (2^9 = 512 <= 1000 < 1024); leaves ceil(1000/2) = 500; parent of 300 is 150, children 600 and 601; depth of 700 = floor(log2 700) = 9 (512 <= 700 < 1024).
2. Check each node vs parent: 5 >= 2, 3 >= 2, 9 >= 5, 4 >= 5? **No** (index 5 holds 4, parent index 2 holds 5). Not a heap.
3. Sorted ascending: every parent index is smaller than the child's index, so its value is <= the child's. A heap only constrains parent/child pairs, so most heaps are not sorted.
</details>

---

## 3. insert and percolate up (6.3.3, Fig 6.6-6.8)

**Worked example first (Fig 6.6/6.7): insert 14 into the heap above.** The engine prints the textbook procedure with index 0 shown:

```
$ python tools/study.py heap insert 13,21,16,24,31,19,68,65,26,32 14
min-heap insert 14

  [0]=14 | 13 21 16 24 31 19 68 65 26 32 _       # insert 14: hole created at index 11; 14 stored in index 0
  [0]=14 | 13 21 16 24 _ 19 68 65 26 32 31       # 14 < parent 31 (index 5) -> slide 31 down to index 11; hole moves to 5
  [0]=14 | 13 _ 16 24 21 19 68 65 26 32 31       # 14 < parent 21 (index 2) -> slide 21 down to index 5; hole moves to 2
  [0]=- | 13 14 16 24 21 19 68 65 26 32 31       # place 14 in index 2 (parent 13 is not larger)

final heap (from index 1): 13,14,16,24,21,19,68,65,26,32,31
```


Read it like this:

1. **Create the hole** at the next free position (index 11 = `currentSize+1`, so the tree stays complete) and store a copy of the new item **14 in index 0**.
2. **Percolate up.** Compare 14 with the parent of the hole (index 11 / 2 = 5, holding 31). 14 < 31, so **slide 31 down into the hole**; the hole moves up to index 5.
3. Parent of index 5 is index 2, holding 21. 14 < 21, so slide 21 down; hole moves to index 2.
4. Parent of index 2 is index 1, holding 13. 14 < 13 is false: **stop**. Put 14 into the hole (index 2). Index 0 is now free again.

**A new minimum climbs all the way to the root.** Here the loop is stopped by the copy in index 0 (that is exactly what the sentinel is for):

```
$ python tools/study.py heap insert 13,21,16,24,31,19,68,65,26,32 5
min-heap insert 5

  [0]=5 | 13 21 16 24 31 19 68 65 26 32 _        # insert 5: hole created at index 11; 5 stored in index 0
  [0]=5 | 13 21 16 24 _ 19 68 65 26 32 31        # 5 < parent 31 (index 5) -> slide 31 down to index 11; hole moves to 5
  [0]=5 | 13 _ 16 24 21 19 68 65 26 32 31        # 5 < parent 21 (index 2) -> slide 21 down to index 5; hole moves to 2
  [0]=5 | _ 13 16 24 21 19 68 65 26 32 31        # 5 < parent 13 (index 1) -> slide 13 down to index 2; hole moves to 1
  [0]=- | 5 13 16 24 21 19 68 65 26 32 31        # place 5 in index 1 (hole is the root)

final heap (from index 1): 5,13,16,24,21,19,68,65,26,32,31
```


**Ties stop** (strict `<`): inserting 21 when the parent chain contains 21 leaves the new 21 *below* the old one:

```
$ python tools/study.py heap insert 13,21,16,24,31,19,68,65,26,32 21
min-heap insert 21

  [0]=21 | 13 21 16 24 31 19 68 65 26 32 _       # insert 21: hole created at index 11; 21 stored in index 0
  [0]=21 | 13 21 16 24 _ 19 68 65 26 32 31       # 21 < parent 31 (index 5) -> slide 31 down to index 11; hole moves to 5
  [0]=- | 13 21 16 24 21 19 68 65 26 32 31       # place 21 in index 5 (parent 21 is not larger)

final heap (from index 1): 13,21,16,24,21,19,68,65,26,32,31
```


### The code (Fig 6.8), line by line

```cpp
1  void insert( const Comparable & x )
2  {
3      if( currentSize == array.size( ) - 1 )
4          array.resize( array.size( ) * 2 );          // grow when full (index 0 is unused, so size-1 slots)
5
6      // Percolate up
7      int hole = ++currentSize;                       // new hole at the next free index
8      Comparable copy = x;
9
10     array[ 0 ] = std::move( copy );                 // sentinel: x is now in cell 0
11     for( ; x < array[ hole / 2 ]; hole /= 2 )       // while x is smaller than the hole's parent
12         array[ hole ] = std::move( array[ hole / 2 ] );   // slide the parent down into the hole
13     array[ hole ] = std::move( array[ 0 ] );        // drop x into its final hole
14 }
```

- Line 7: `++currentSize` first, so `hole` = index of the new last position. This is the O(1) "add at the end" step.
- Line 10: copy of x in cell 0. When the hole reaches the root, `hole/2 = 0` and the test is `x < array[0]` = `x < x` = false, so the loop **stops without a separate `hole > 1` test**.
  That is the only reason cell 0 exists. (HW6 6.5 asks you to rewrite insert with this sentinel; see section 12.)
- Line 11-12: the "hole moves up" trick. Swapping would cost 3 assignments per level; sliding costs 1, so a rise of d levels costs **d+1 assignments, not 3d**.
- Line 13: write x (from cell 0, which still holds it) into the hole.
- Duplicates are allowed; `<` is strict, so an equal parent stops the loop.

**Cost.** O(log N) worst case (the new item is the new minimum and rises through all floor(log2 N) levels). **O(1) average** (section 7). The textbook quotes
2.607 comparisons on average (the item rises about 1.607 levels).

**Check yourself**
1. Insert 4 into the min-heap 3,5,7,9,6 (indices 1-5). Show the array with index 0 after each step. 2. How many assignments does a rise of 5 levels cost with the hole method versus swaps? 3. What goes wrong if `array[0]` isn't set?

<details><summary>Answer</summary>

1. Engine output:

```
$ python tools/study.py heap insert 3,5,7,9,6 4
min-heap insert 4

  [0]=4 | 3 5 7 9 6 _                            # insert 4: hole created at index 6; 4 stored in index 0
  [0]=4 | 3 5 _ 9 6 7                            # 4 < parent 7 (index 3) -> slide 7 down to index 6; hole moves to 3
  [0]=- | 3 5 4 9 6 7                            # place 4 in index 3 (parent 3 is not larger)

final heap (from index 1): 3,5,4,9,6,7
```

2. Hole method: d + 1 = 6 assignments (5 slides + final placement). Swaps: 3d = 15. 3. The loop would compare against whatever junk is in index 0 and could keep going past the root (or stop wrongly).
</details>

---

## 4. deleteMin and percolate down (6.3.3, Fig 6.9-6.12) - and the HW6 Q2 step format

<!-- HOLD hw6 -->
**Worked example first: HW6 Question 2.** Delete the 3 at the root of the min-heap `3, 6, 5, 7, 12, 9, 13, 11, 8` (indices 1-9). **Show the array after each step, index 0 holds
the value being moved.** The engine's output is exactly the format to hand in:

```
$ python tools/study.py heap delete 3,6,5,7,12,9,13,11,8 --count 1
min-heap deleteMin x1 (removed [3])

  [0]=8 | _ 6 5 7 12 9 13 11                     # deleteMin: remove 3 from the root (hole at 1); last element 8 goes to index 0; size 8
  [0]=8 | 5 6 _ 7 12 9 13 11                     # smaller child 5 (index 3) beats 8 -> slide it up to index 1; hole moves to 3
  [0]=8 | 5 6 _ 7 12 9 13 11                     # best child 9 (index 6) does not beat 8 -> stop
  [0]=- | 5 6 8 7 12 9 13 11                     # place 8 in index 3

final heap (from index 1): 5,6,8,7,12,9,13,11
```


Walk-through (initial array: `[0]=- | 3 6 5 7 12 9 13 11 8`, size 9):

1. **Remove the minimum 3 at the root; the heap shrinks to 8 elements, so the last element (8, index 9) must be placed somewhere.** Put **8 in index 0**; the root is a hole: `[0]=8 | _ 6 5 7 12 9 13 11` (index 9 is gone).
2. **Percolate down.** The hole is at index 1; children are index 2 (6) and index 3 (5). Smaller child = 5 (index 3). 5 < 8, so slide 5 **up** into the hole; the hole moves to index 3.
3. Hole at index 3; its children are index 6 (9) and index 7 (13). Smaller child = 9. 9 < 8 is false: **stop**.
4. Put 8 into the hole (index 3), clear index 0: `5 6 8 7 12 9 13 11`.

Final heap: `5, 6, 8, 7, 12, 9, 13, 11`.

**A longer example (Fig 6.9-6.11):** delete 13 from the 11-element heap of Figure 6.9 (the last element is 31). The element 31 percolates almost all the way to the bottom,
which is typical (it came from the bottom, so it belongs near the bottom).

```
$ python tools/study.py heap delete 13,14,16,19,21,19,68,65,26,32,31 --count 1
min-heap deleteMin x1 (removed [13])

  [0]=31 | _ 14 16 19 21 19 68 65 26 32          # deleteMin: remove 13 from the root (hole at 1); last element 31 goes to index 0; size 10
  [0]=31 | 14 _ 16 19 21 19 68 65 26 32          # smaller child 14 (index 2) beats 31 -> slide it up to index 1; hole moves to 2
  [0]=31 | 14 19 16 _ 21 19 68 65 26 32          # smaller child 19 (index 4) beats 31 -> slide it up to index 2; hole moves to 4
  [0]=31 | 14 19 16 26 21 19 68 65 _ 32          # smaller child 26 (index 9) beats 31 -> slide it up to index 4; hole moves to 9
  [0]=- | 14 19 16 26 21 19 68 65 31 32          # place 31 in index 9

final heap (from index 1): 14,19,16,26,21,19,68,65,31,32
```


**The one-child trap.** When the heap size is even, the last internal node has only a left child. Delete from a 15-element heap (size becomes 14): the hole reaches index 7, whose only
child is index 14 = `currentSize`. The code must not read `array[15]`:

```
$ python tools/study.py heap delete 1,3,2,6,7,5,4,15,14,12,9,10,11,13,8 --count 1
min-heap deleteMin x1 (removed [1])

  [0]=8 | _ 3 2 6 7 5 4 15 14 12 9 10 11 13      # deleteMin: remove 1 from the root (hole at 1); last element 8 goes to index 0; size 14
  [0]=8 | 2 3 _ 6 7 5 4 15 14 12 9 10 11 13      # smaller child 2 (index 3) beats 8 -> slide it up to index 1; hole moves to 3
  [0]=8 | 2 3 4 6 7 5 _ 15 14 12 9 10 11 13      # smaller child 4 (index 7) beats 8 -> slide it up to index 3; hole moves to 7
  [0]=8 | 2 3 4 6 7 5 _ 15 14 12 9 10 11 13      # best child 13 (index 14) does not beat 8 -> stop
  [0]=- | 2 3 4 6 7 5 8 15 14 12 9 10 11 13      # place 8 in index 7

final heap (from index 1): 2,3,4,6,7,5,8,15,14,12,9,10,11,13
```


<!-- /HOLD -->

### The code (Fig 6.12), line by line

```cpp
10  array[ 1 ] = std::move( array[ currentSize-- ] );  // last element goes into the root slot; size shrinks by one
11  percolateDown( 1 );

32  void percolateDown( int hole )
33  {
34      int child;
35      Comparable tmp = std::move( array[ hole ] );   // the value being moved (HW6 stores it in index 0)
36
37      for( ; hole * 2 <= currentSize; hole = child ) // while the hole has at least a left child
38      {
39          child = hole * 2;                          // left child
40          if( child != currentSize && array[ child + 1 ] < array[ child ] )
41              ++child;                               // right child exists and is strictly smaller: use it
42          if( array[ child ] < tmp )
43              array[ hole ] = std::move( array[ child ] );   // smaller child moves UP into the hole
44          else
45              break;                                 // tmp belongs here
46      }
47      array[ hole ] = std::move( tmp );              // place the value in the final hole
48  }
```

- Line 10: `currentSize--` is post-decrement: reads the last element, then shrinks. For a one-element heap this copies the only element onto itself and the heap becomes empty.
- Line 37: `hole*2 <= currentSize` = "the hole has a left child".
- Line 40: **`child != currentSize`** means the left child is the very last element, so there is **no right child**. Forgetting it reads past the heap: the book's "frequent implementation error".
  `array[child+1] < array[child]` is strict, so **equal children go left**.
- Line 42: `<` strict: if the child equals tmp, tmp stays (ties stop).
- Two comparisons per level (child vs child, child vs tmp): the book counts 2 log N comparisons worst case.

**Cost.** O(log N) worst case. Also O(log N) on **average** (the book: the moved element came from the bottom, so it usually percolates almost to the bottom).

**Check yourself**
1. Delete the min of `2, 4, 3, 8, 5, 6`; show the array with index 0 after each step. 2. In `percolateDown` how many comparisons does one level use? 3. Which line prevents reading out of bounds?

<details><summary>Answer</summary>

1. Engine output:

```
$ python tools/study.py heap delete 2,4,3,8,5,6 --count 1
min-heap deleteMin x1 (removed [2])

  [0]=6 | _ 4 3 8 5                              # deleteMin: remove 2 from the root (hole at 1); last element 6 goes to index 0; size 5
  [0]=6 | 3 4 _ 8 5                              # smaller child 3 (index 3) beats 6 -> slide it up to index 1; hole moves to 3
  [0]=- | 3 4 6 8 5                              # place 6 in index 3

final heap (from index 1): 3,4,6,8,5
```

2. Two per level (smaller child; then smaller child vs tmp). 3. Line 40, `child != currentSize` (and line 37 for the case of no children).
</details>

---

## 5. buildHeap: O(N), and why it is not O(N log N) (6.3.4, Fig 6.14-6.18, slides "BuildHeap")

N insertions cost O(N log N) worst case. If all items are known up front there is a smarter way: dump them in the array in any order (that already satisfies the **structure**
property), then fix the **order** property from the bottom up.

**Worked example first: Fig 6.15-6.18 of the book** (input `150 80 40 30 10 70 110 100 20 90 60 50 120 140 130`, N = 15, so percolateDown for i = 7 down to 1):

```
$ python tools/study.py heap build 150,80,40,30,10,70,110,100,20,90,60,50,120,140,130
buildHeap (min-heap)

  [0]=- | 150 80 40 30 10 70 110 100 20 90 60 50 120 140 130 # start (size 15); percolateDown from i = 7 down to 1
  [0]=- | 150 80 40 30 10 70 110 100 20 90 60 50 120 140 130 # after percolateDown(7) (value 110)
  [0]=- | 150 80 40 30 10 50 110 100 20 90 60 70 120 140 130 # after percolateDown(6) (value 70)
  [0]=- | 150 80 40 30 10 50 110 100 20 90 60 70 120 140 130 # after percolateDown(5) (value 10)
  [0]=- | 150 80 40 20 10 50 110 100 30 90 60 70 120 140 130 # after percolateDown(4) (value 30)
  [0]=- | 150 80 40 20 10 50 110 100 30 90 60 70 120 140 130 # after percolateDown(3) (value 40)
  [0]=- | 150 10 40 20 60 50 110 100 30 90 80 70 120 140 130 # after percolateDown(2) (value 80)
  [0]=- | 10 20 40 30 60 50 110 100 150 90 80 70 120 140 130 # after percolateDown(1) (value 150)

final heap (from index 1): 10,20,40,30,60,50,110,100,150,90,80,70,120,140,130
```


The same, with every slide shown (only when asked for details); a smaller input, 7 elements, so i = 3, 2, 1:

```
$ python tools/study.py heap build 8,5,9,2,6,3,7 --detail
buildHeap (min-heap)

  [0]=- | 8 5 9 2 6 3 7                          # start (size 7); percolateDown from i = 3 down to 1
  [0]=9 | 8 5 _ 2 6 3 7                          # percolateDown(3): 9 moved to index 0, hole at 3
  [0]=9 | 8 5 3 2 6 _ 7                          # smaller child 3 (index 6) beats 9 -> slide it up to index 3; hole moves to 6
  [0]=- | 8 5 3 2 6 9 7                          # place 9 in index 6
  [0]=5 | 8 _ 3 2 6 9 7                          # percolateDown(2): 5 moved to index 0, hole at 2
  [0]=5 | 8 2 3 _ 6 9 7                          # smaller child 2 (index 4) beats 5 -> slide it up to index 2; hole moves to 4
  [0]=- | 8 2 3 5 6 9 7                          # place 5 in index 4
  [0]=8 | _ 2 3 5 6 9 7                          # percolateDown(1): 8 moved to index 0, hole at 1
  [0]=8 | 2 _ 3 5 6 9 7                          # smaller child 2 (index 2) beats 8 -> slide it up to index 1; hole moves to 2
  [0]=8 | 2 5 3 _ 6 9 7                          # smaller child 5 (index 4) beats 8 -> slide it up to index 2; hole moves to 4
  [0]=- | 2 5 3 8 6 9 7                          # place 8 in index 4

final heap (from index 1): 2,5,3,8,6,9,7
```


What happened: the leaves (indices 4..7) are already one-element heaps, so start at the last internal node `N/2 = 3`. Each `percolateDown(i)` assumes both subtrees of `i` are
already heaps and sinks `array[i]` to its place, so after it the subtree at `i` is a heap. Finishing with `i = 1` makes the whole array a heap (induction, slides "first we must prove that...").

### The code (Fig 6.14)

```cpp
13  void buildHeap( )
14  {
15      for( int i = currentSize / 2; i > 0; --i )     // last internal node down to the root
16          percolateDown( i );
17  }
```

(The constructor copies the N items into `array[1..N]` and calls `buildHeap`.) Starting at `N/2` skips all leaves (they have nowhere to go): half the nodes cost 0.

### Why it is O(N) - the proof you must be able to write

**Naive (loose) bound:** N/2 calls x O(log N) each = O(N log N). **True bound:** the cost of `percolateDown(i)` is at most the **height of node i** (how far it can sink), not log N.
Total cost <= **sum of the heights of all nodes**.

*Slides' version.* In a complete tree about N/2 nodes are leaves (height 0, cost 0), N/4 nodes have height 1, N/8 have height 2, N/16 have height 3, ...

```
cost <= 0*(N/2) + 1*(N/4) + 2*(N/8) + 3*(N/16) + 4*(N/32) + ...
      = N/4 + N/8 + N/16 + N/32 + ...        (= N/2)
            + N/8 + N/16 + N/32 + ...        (= N/4)
                  + N/16 + N/32 + ...        (= N/8)
                         + ...               (= N/16) ...
      = N/2 + N/4 + N/8 + N/16 + ... = N
```

Each line is a geometric series; the column sums are the same as taking the nodes of height >= 1, >= 2, >= 3, ...: the number of nodes of height >= k is about N/2^k.

*Textbook version (Theorem 6.1).* For a **perfect** tree of height h (N = 2^(h+1) - 1 nodes) there is 1 node of height h, 2 of height h-1, 4 of height h-2, ..., 2^h of height 0:

```
S = sum_{i=0..h} 2^i (h - i) = h + 2(h-1) + 4(h-2) + ... + 2^(h-1)(1)
2S =    2h + 4(h-1) + 8(h-2) + ... + 2^h (1)
2S - S = -h + 2 + 4 + 8 + ... + 2^(h-1) + 2^h = (2^(h+1) - 1) - (h + 1)
```

so **S = N - (h+1) < N**. A complete tree has between 2^h and 2^(h+1) nodes, so its sum of heights is at most this, which is **O(N)**. (Book: for a complete tree the sum is exactly N - b(N), b(N) = number of 1s in the binary representation of N; since b(N) >= 1, it is at most N-1.)

**Compare:** `buildHeap` O(N) worst case; N successive `insert`s O(N log N) worst case (but O(N) average). Worst-case input for N inserts into a min-heap: **decreasing** keys, every new key rises to the root:

```
$ python tools/study.py heap insert "" 7,6,5,4,3,2,1
min-heap insert 7,6,5,4,3,2,1

  [0]=7 | _                                      # insert 7: hole created at index 1; 7 stored in index 0
  [0]=- | 7                                      # place 7 in index 1 (hole is the root)
  [0]=6 | 7 _                                    # insert 6: hole created at index 2; 6 stored in index 0
  [0]=6 | _ 7                                    # 6 < parent 7 (index 1) -> slide 7 down to index 2; hole moves to 1
  [0]=- | 6 7                                    # place 6 in index 1 (hole is the root)
  [0]=5 | 6 7 _                                  # insert 5: hole created at index 3; 5 stored in index 0
  [0]=5 | _ 7 6                                  # 5 < parent 6 (index 1) -> slide 6 down to index 3; hole moves to 1
  [0]=- | 5 7 6                                  # place 5 in index 1 (hole is the root)
  [0]=4 | 5 7 6 _                                # insert 4: hole created at index 4; 4 stored in index 0
  [0]=4 | 5 _ 6 7                                # 4 < parent 7 (index 2) -> slide 7 down to index 4; hole moves to 2
  [0]=4 | _ 5 6 7                                # 4 < parent 5 (index 1) -> slide 5 down to index 2; hole moves to 1
  [0]=- | 4 5 6 7                                # place 4 in index 1 (hole is the root)
  [0]=3 | 4 5 6 7 _                              # insert 3: hole created at index 5; 3 stored in index 0
  [0]=3 | 4 _ 6 7 5                              # 3 < parent 5 (index 2) -> slide 5 down to index 5; hole moves to 2
  [0]=3 | _ 4 6 7 5                              # 3 < parent 4 (index 1) -> slide 4 down to index 2; hole moves to 1
  [0]=- | 3 4 6 7 5                              # place 3 in index 1 (hole is the root)
  [0]=2 | 3 4 6 7 5 _                            # insert 2: hole created at index 6; 2 stored in index 0
  [0]=2 | 3 4 _ 7 5 6                            # 2 < parent 6 (index 3) -> slide 6 down to index 6; hole moves to 3
  [0]=2 | _ 4 3 7 5 6                            # 2 < parent 3 (index 1) -> slide 3 down to index 3; hole moves to 1
  [0]=- | 2 4 3 7 5 6                            # place 2 in index 1 (hole is the root)
  [0]=1 | 2 4 3 7 5 6 _                          # insert 1: hole created at index 7; 1 stored in index 0
  [0]=1 | 2 4 _ 7 5 6 3                          # 1 < parent 3 (index 3) -> slide 3 down to index 7; hole moves to 3
  [0]=1 | _ 4 2 7 5 6 3                          # 1 < parent 2 (index 1) -> slide 2 down to index 3; hole moves to 1
  [0]=- | 1 4 2 7 5 6 3                          # place 1 in index 1 (hole is the root)

final heap (from index 1): 1,4,2,7,5,6,3
```


Each of the last six inserts rose to the root (1, 1, 2, 2, 2, 2 levels), and with N keys the rises are 0, 1, 1, 2, 2, 2, 2, 3 ... ~ log(N!) = Theta(N log N) in total.

**Max-heap build** (same code with `>`; used by heapsort):

```
$ python tools/study.py heap build 10,12,1,14,6,5,8,15,3,9,7 --max
buildHeap (max-heap)

  [0]=- | 10 12 1 14 6 5 8 15 3 9 7              # start (size 11); percolateDown from i = 5 down to 1
  [0]=- | 10 12 1 14 9 5 8 15 3 6 7              # after percolateDown(5) (value 6)
  [0]=- | 10 12 1 15 9 5 8 14 3 6 7              # after percolateDown(4) (value 14)
  [0]=- | 10 12 8 15 9 5 1 14 3 6 7              # after percolateDown(3) (value 1)
  [0]=- | 10 15 8 14 9 5 1 12 3 6 7              # after percolateDown(2) (value 12)
  [0]=- | 15 14 8 12 9 5 1 10 3 6 7              # after percolateDown(1) (value 10)

final heap (from index 1): 15,14,8,12,9,5,1,10,3,6,7
```


Comparisons: each level of a percolateDown is 2 element comparisons, so buildHeap does at most `2 x (sum of heights) <= 2N - 2` comparisons (HW 6.7a, section 12).

**Check yourself**
1. Run buildHeap on `7, 3, 9, 1, 5, 2` (min-heap, indices 1-6). Show the array after each percolateDown. 2. Why does the loop start at N/2 and not N? 3. Why is "N/2 calls x log N" a correct but not tight bound?

<details><summary>Answer</summary>

1. Engine output:

```
$ python tools/study.py heap build 7,3,9,1,5,2
buildHeap (min-heap)

  [0]=- | 7 3 9 1 5 2                            # start (size 6); percolateDown from i = 3 down to 1
  [0]=- | 7 3 2 1 5 9                            # after percolateDown(3) (value 9)
  [0]=- | 7 1 2 3 5 9                            # after percolateDown(2) (value 3)
  [0]=- | 1 3 2 7 5 9                            # after percolateDown(1) (value 7)

final heap (from index 1): 1,3,2,7,5,9
```

2. Indices N/2+1..N are leaves (a node has a child iff 2i <= N); a leaf is already a heap. 3. Most calls start near the bottom and move only 0, 1, 2 levels; only one node (the root) can move log N levels. The sum of heights is O(N).
</details>

---

## 6. decreaseKey, increaseKey, remove (6.3.4) - they need the position

A heap cannot search, so these assume **you already know the index p** of the element (keep a hash table value -> index alongside if you need that). All three are O(log N) **worst case**.

| Operation | Steps | Cost |
|---|---|---|
| `decreaseKey(p, d)` | `array[p] -= d`; **percolate up** from p | O(log N) |
| `increaseKey(p, d)` | `array[p] += d`; **percolate down** from p | O(log N) |
| `remove(p)` | `decreaseKey(p, infinity)` (the element bubbles to the root) then `deleteMin()` | O(log N) |

The book gives no code for these (only the description); they reuse the same hole mechanics. Example: heap `13,14,16,24,21,19,68,65,26,32,31`.

**decreaseKey(10, 12):** index 10 holds 32, becomes 20, rises one level past 21 (the parent):

```
$ python tools/study.py heap decrease 13,14,16,24,21,19,68,65,26,32,31 10 12
decreaseKey(10, 12)

  [0]=- | 13 14 16 24 21 19 68 65 26 20 31       # decreaseKey(10, 12): index 10 becomes 20
  [0]=20 | 13 14 16 24 _ 19 68 65 26 21 31       # slide parent 21 down to index 10
  [0]=- | 13 14 16 24 20 19 68 65 26 21 31       # place 20 in index 5

final heap (from index 1): 13,14,16,24,20,19,68,65,26,21,31
```


**decreaseKey(9, 20):** index 9 holds 26, becomes 6, which is a new minimum, so it rises to the root:

```
$ python tools/study.py heap decrease 13,14,16,24,21,19,68,65,26,32,31 9 20
decreaseKey(9, 20)

  [0]=- | 13 14 16 24 21 19 68 65 6 32 31        # decreaseKey(9, 20): index 9 becomes 6
  [0]=6 | 13 14 16 _ 21 19 68 65 24 32 31        # slide parent 24 down to index 9
  [0]=6 | 13 _ 16 14 21 19 68 65 24 32 31        # slide parent 14 down to index 4
  [0]=6 | _ 13 16 14 21 19 68 65 24 32 31        # slide parent 13 down to index 2
  [0]=- | 6 13 16 14 21 19 68 65 24 32 31        # place 6 in index 1

final heap (from index 1): 6,13,16,14,21,19,68,65,24,32,31
```


**increaseKey(2, 20):** index 2 holds 14, becomes 34, and sinks to the bottom:

```
$ python tools/study.py heap increase 13,14,16,24,21,19,68,65,26,32,31 2 20
increaseKey(2, 20)

  [0]=- | 13 34 16 24 21 19 68 65 26 32 31       # increaseKey(2, 20): index 2 becomes 34
  [0]=34 | 13 _ 16 24 21 19 68 65 26 32 31       # percolateDown(2): 34 moved to index 0, hole at 2
  [0]=34 | 13 21 16 24 _ 19 68 65 26 32 31       # smaller child 21 (index 5) beats 34 -> slide it up to index 2; hole moves to 5
  [0]=34 | 13 21 16 24 31 19 68 65 26 32 _       # smaller child 31 (index 11) beats 34 -> slide it up to index 5; hole moves to 11
  [0]=- | 13 21 16 24 31 19 68 65 26 32 34       # place 34 in index 11

final heap (from index 1): 13,21,16,24,31,19,68,65,26,32,34
```


**remove(5)** (the 21): bubble to the root as "minus infinity", then run deleteMin (the last element, 31, goes to index 0 and percolates down):

```
$ python tools/study.py heap remove 13,14,16,24,21,19,68,65,26,32,31 5
remove(index 5) = 21

  [0]=- | 13 14 16 24 _ 19 68 65 26 32 31        # remove(5): 21 becomes -infinity (decreaseKey by infinity) and percolates up
  [0]=- | 13 _ 16 24 14 19 68 65 26 32 31        # slide parent 14 down to index 5
  [0]=- | _ 13 16 24 14 19 68 65 26 32 31        # slide parent 13 down to index 2
  [0]=- | -inf 13 16 24 14 19 68 65 26 32 31     # the -infinity value is at the root; now deleteMin removes it
  [0]=31 | 13 _ 16 24 14 19 68 65 26 32          # smaller child 13 (index 2) beats 31 -> slide it up to index 1; hole moves to 2
  [0]=31 | 13 14 16 24 _ 19 68 65 26 32          # smaller child 14 (index 5) beats 31 -> slide it up to index 2; hole moves to 5
  [0]=31 | 13 14 16 24 _ 19 68 65 26 32          # best child 32 (index 10) does not beat 31 -> stop
  [0]=- | 13 14 16 24 31 19 68 65 26 32          # place 31 in index 5

final heap (from index 1): 13,14,16,24,31,19,68,65,26,32
```


Other costs: `findMin` O(1); finding an **arbitrary** item or the **maximum** (it is at some leaf, but nothing says which) is a linear scan, O(N); merging two heaps is O(N) in an array heap
(the textbook's leftist/skew/binomial heaps, 6.5+, are out of scope). Real use: schedulers lower/raise priorities (`increaseKey` after a process hogs the CPU); a user killing a process needs `remove`.

**Check yourself**
1. Min-heap `2,5,3,9,8,4`. Do `decreaseKey(5, 5)` (index 5 holds 8). 2. Why is `increaseKey` on a min-heap a percolate **down**?

<details><summary>Answer</summary>

1. Engine output (the 8 becomes 3, rises past 5, and stops under the root 2):

```
$ python tools/study.py heap decrease 2,5,3,9,8,4 5 5
decreaseKey(5, 5)

  [0]=- | 2 5 3 9 3 4                            # decreaseKey(5, 5): index 5 becomes 3
  [0]=3 | 2 _ 3 9 5 4                            # slide parent 5 down to index 5
  [0]=- | 2 3 3 9 5 4                            # place 3 in index 2

final heap (from index 1): 2,3,3,9,5,4
```

2. A bigger key may now exceed its children, which violates order below it; it can still be >= its parent, so only the downward direction can break.
</details>

---

## 7. Average-case O(1) insert, and when the argument fails (slides "Proof of O(1) Average Insert")

Two parts to the claim:

1. **Placing** the new element at the end of the array is O(1).
2. **Percolate up** moves it a *constant* number of levels **on average** (it can take up to log N steps in the worst case: a new minimum).

Intuition (same style of argument as buildHeap): half the nodes are leaves and the new element starts at the bottom level. For it to rise j levels it must be smaller than its ancestor j levels
up, which is the *minimum of a subtree of about 2^(j+1) elements*. If the new value has the same random distribution as the ones in the heap, the chance of beating that minimum is
about 1/2^(j+1), so the expected number of levels it rises is a convergent sum, about sum_{j>=1} 2^-(j+1) = O(1). (The book states the measured/derived value: about 1.607 levels, 2.607 comparisons.)
Consequently **N inserts cost O(N) on average** (but O(N log N) worst case) - the same bound buildHeap guarantees in the worst case.

**When it does NOT apply** (slide's warning, and a likely short-answer question):

- The inserted values must come from **the same distribution** as the values already in the heap. **Sorted decreasing input** into a min-heap (see the engine trace in section 5) rises to the root every time: Theta(log N) per insert.
  (Sorted **increasing** input is the lucky case: no rise at all, O(1) each, worst case too.)
- **Alternating inserts and deleteMins**: every deleteMin removes the smallest element, so the elements left behind are *larger* than a fresh random element, and new elements tend to rise far.
  The O(1) average does not hold for a mix of insert/deleteMin; use O(log N) per operation.
- deleteMin has **no** such saving: O(log N) average and worst (the element moved to the root came from the bottom and sinks back to the bottom).

**Check yourself**
1. A program does N inserts of random keys into an empty min-heap. Average total cost? 2. Same, but keys arrive in decreasing order? 3. Alternate N inserts and N deleteMins on a heap of size N?

<details><summary>Answer</summary>

1. O(N) (average O(1) each). 2. Theta(N log N): each insert percolates to the root. 3. O(N log N): each of the 2N operations costs O(log N); the average-O(1) argument is invalid here.
</details>

---

## 8. Applications of priority queues (6.4)

### 8.1 The selection problem (6.4.1): k-th largest/smallest of N elements

Baselines from Ch 1: 1A = sort everything, O(N log N) with a good sort (the book says O(N^2) assuming a simple sort); 1B = keep a sorted array of the k largest, O(N k).

**Algorithm 6A (k-th smallest): buildHeap on all N elements, then k deleteMins.** The k-th one removed is the answer.

- buildHeap O(N) + k deleteMin x O(log N) = **O(N + k log N)**.
- If k = O(N / log N) the buildHeap dominates: O(N). For k = N/2 (the median): Theta(N log N). For k = N, recording the values as they leave = sorting in O(N log N) = heapsort (note 06).
- For the k-th **largest**, use a **max**-heap (or reverse the comparisons).

**Algorithm 6B (k-th largest): keep a heap S of the k largest seen so far.** Read the first k elements into a heap with buildHeap (O(k)). For every later element x: compare with the smallest of S (`findMin`, O(1)); if x is larger,
`deleteMin` then `insert x` (O(log k)). At the end, the root of S is the answer. Since S must expose its **smallest** element, S is a **min-heap**, even though we want the k *largest*.

- Cost: O(k) + (N - k) x [O(1) test + O(log k) update] = **O(k + (N - k) log k) = O(N log k)**; space O(k); works on a stream.
- For the median (k = N/2): Theta(N log N), no better than 6A. Good when k is small (k = 10 of a billion: O(N) with tiny constants).
- Both are O(N log N) at k = N/2; the book notes quickselect (Ch 7) gets O(N) **average** (O(N^2) worst), and that is why the slides say quickselect beats the heap-based algorithms for the median.

| Algorithm | Time | Extra space | Best when |
|---|---|---|---|
| 6A: buildHeap + k deleteMin | O(N + k log N) | O(1) if done in place | k small or all data already in memory |
| 6B: size-k heap, one pass | O(N log k) | O(k) | k much smaller than N; streaming data |
| Quickselect (Ch 7) | O(N) average, O(N^2) worst | O(1) | median / large k |

STL versions (min-heap = `greater<int>`; `priority_queue` is a **max**-heap by default):

```cpp
#include <queue>
#include <vector>
#include <functional>

// 6B: k-th largest in O(N log k) time, O(k) space.
int kthLargest(const std::vector<int> & nums, int k) {
    std::priority_queue<int, std::vector<int>, std::greater<int>> minHeap;   // top() = smallest of the k kept
    for (int x : nums) {
        if ((int) minHeap.size() < k)
            minHeap.push(x);                       // O(log k)
        else if (x > minHeap.top()) {              // O(1) test
            minHeap.pop();                         // O(log k)
            minHeap.push(x);                       // O(log k)
        }
    }
    return minHeap.top();                          // O(1); assumes 1 <= k <= nums.size()
}
```

### 8.2 Event simulation (6.4.2) - high level

Simulate a bank with k tellers: events are "customer arrives" and "customer departs". Ticking a clock one unit at a time costs time proportional to the number of ticks (not the input size).
Instead **jump to the next event time**: keep the pending departures in a **priority queue ordered by event time** (smallest time first). The next event is the earlier of (next arrival from the input, smallest departure in the heap).
A departure frees a teller and may start the next waiting customer (computes a new departure time, inserted into the heap); an arrival either takes a free teller (insert its departure) or joins an ordinary FIFO queue.
With C customers (2C events) and at most k+1 events in the heap, the total is **O(C log(k+1))** because each event costs O(log H), H = heap size.

### 8.3 Others (only mention)

Operating-system schedulers (decreaseKey/increaseKey), greedy algorithms and Dijkstra (later chapters), external sorting with replacement selection (7.12), and heapsort itself.

**Check yourself**
1. N = 10^6, k = 5. Which of 6A/6B is better and what is its running time? 2. Same N, k = N/2. 3. Why must the heap in 6B be a *min*-heap?

<details><summary>Answer</summary>

1. 6B: O(N log k) = O(N log 5) = O(N), one pass, O(k) space. (6A is also O(N + k log N) = O(N) here; both are linear, 6B uses much less memory.) 2. Both Theta(N log N); quickselect gives O(N) average. 3. We evict the smallest of the k kept, so the heap must expose its minimum in O(1) and remove it in O(log k).
</details>

---

## 9. The max-heap variant

Reverse every comparison: parent >= children, the **maximum is at the root**, `deleteMax` (`>` in place of `<`). Textbook footnote 2: a priority queue finds the minimum *or* the maximum, decided in advance.
Everything else (layout, hole technique, O(1)/O(log N)/O(N) costs) is identical.

```
$ python tools/study.py heap delete 15,14,8,12,9,5,1,10,3,6,7 --count 2 --max
max-heap deleteMax x2 (removed [15, 14])

  [0]=7 | _ 14 8 12 9 5 1 10 3 6                 # deleteMax: remove 15 from the root (hole at 1); last element 7 goes to index 0; size 10
  [0]=7 | 14 _ 8 12 9 5 1 10 3 6                 # larger child 14 (index 2) beats 7 -> slide it up to index 1; hole moves to 2
  [0]=7 | 14 12 8 _ 9 5 1 10 3 6                 # larger child 12 (index 4) beats 7 -> slide it up to index 2; hole moves to 4
  [0]=7 | 14 12 8 10 9 5 1 _ 3 6                 # larger child 10 (index 8) beats 7 -> slide it up to index 4; hole moves to 8
  [0]=- | 14 12 8 10 9 5 1 7 3 6                 # place 7 in index 8
  [0]=6 | _ 12 8 10 9 5 1 7 3                    # deleteMax: remove 14 from the root (hole at 1); last element 6 goes to index 0; size 9
  [0]=6 | 12 _ 8 10 9 5 1 7 3                    # larger child 12 (index 2) beats 6 -> slide it up to index 1; hole moves to 2
  [0]=6 | 12 10 8 _ 9 5 1 7 3                    # larger child 10 (index 4) beats 6 -> slide it up to index 2; hole moves to 4
  [0]=6 | 12 10 8 7 9 5 1 _ 3                    # larger child 7 (index 8) beats 6 -> slide it up to index 4; hole moves to 8
  [0]=- | 12 10 8 7 9 5 1 6 3                    # place 6 in index 8

final heap (from index 1): 12,10,8,7,9,5,1,6,3
```


- **In STL:** `priority_queue<int>` is a **max**-heap (`top()` = largest); a min-heap is `priority_queue<int, vector<int>, greater<int>>`. `push`/`pop` O(log n), `top` O(1).
  Library heap functions on a `vector`: `make_heap` O(n), `push_heap` O(log n), `pop_heap` O(log n) (moves the root to the back), `sort_heap` O(n log n); default comparator `<` gives a **max**-heap.
- Heapsort (Ch 7) uses a **max**-heap stored 0-indexed; see `06-heapsort-introsort.md`.

---

## 10. Complexity table

| Operation (N elements) | Worst case | Average | One-line reason |
|---|---|---|---|
| findMin | O(1) | O(1) | root |
| insert | O(log N) | **O(1)** | O(1) placement + percolate up (<= height; constant on average for same-distribution keys) |
| deleteMin | O(log N) | O(log N) | percolate down from root, moved element came from the bottom |
| buildHeap | **O(N)** | O(N) | sum of node heights < N; **not** N log N |
| N inserts (one by one) | O(N log N) | O(N) | decreasing input is worst |
| decreaseKey / increaseKey / remove (position known) | O(log N) | O(log N) | one percolate up / down (remove = decreaseKey + deleteMin) |
| find arbitrary item / findMax | O(N) | O(N) | heap order says nothing across subtrees; max is at a leaf, ceil(N/2) candidates |
| merge two heaps | O(N) | O(N) | rebuild (needs leftist/skew/binomial for O(log N); out of scope) |
| Selection 6A / 6B | O(N + k log N) / O(N log k) | | see 8.1 |
| STL `priority_queue` push / pop / top | O(log n) / O(log n) / O(1) | | |
| STL `make_heap` / `push_heap` / `pop_heap` / `sort_heap` | O(n) / O(log n) / O(log n) / O(n log n) | | |

---

## 11. Traps that cost points

1. **Index 0.** Textbook heaps start at **1**. Index 0 holds the moved/sentinel value in a trace. Heapsort's array (Ch 7) starts at **0**. Do not mix them: children `2i, 2i+1` versus `2i+1, 2i+2`.
2. **Forgetting the one-child case** (`child != currentSize`) when the heap size is even.
3. **Ties.** Insert: strict `<`, equal parent stops. deleteMin: the right child is used only if **strictly smaller** than the left child; equal children => the **left** one moves up. Stop when the child is **not strictly smaller** than tmp.
4. **buildHeap is O(N), not O(N log N)**, and the justification is the sum of heights (explain it; do not just say "it is linear").
5. **Insert is O(1) only on average**, O(log N) worst case; and only for same-distribution inserts, not alternating inserts/deleteMins.
6. **deleteMin moves the LAST element to the root, not the smaller child up through the tree by swapping.** Do not "delete the root and promote children" (that leaves a non-complete tree).
7. buildHeap percolates **down** from N/2 **to 1**; going in the other direction, or percolating up, is wrong.
8. A heap is **not sorted**, and finding the max in a min-heap is O(N) (a leaf), not O(1) or O(log N).
9. `priority_queue` is a **max**-heap by default; for a min-heap write the 3-argument form with `greater<int>`.
10. To get the k **largest** elements you keep a **min**-heap of size k (6B).
11. "Insert N elements" in a design question: if they are all known up front, say `make_heap`/buildHeap O(N), not N pushes O(N log N).
12. The textbook implementation is what the exam wants: a different "valid" variant (e.g. 0-indexed children `2i+1` in a Ch 6 question, swapping instead of the hole) is graded wrong.

---

<!-- HOLD hw6 -->
## 12. HW6 worked answers

**6.1** Can insert and findMin both be O(1)? See section 1: yes with an unsorted list plus a min variable (deleteMin then costs O(N)).

**6.2a** Insert 10, 12, 1, 14, 6, 5, 8, 15, 3, 9, 7, 4, 11, 13, 2 one at a time into an empty min-heap:

```
$ python tools/study.py heap insert "" 10,12,1,14,6,5,8,15,3,9,7,4,11,13,2
min-heap insert 10,12,1,14,6,5,8,15,3,9,7,4,11,13,2

  [0]=10 | _                                     # insert 10: hole created at index 1; 10 stored in index 0
  [0]=- | 10                                     # place 10 in index 1 (hole is the root)
  [0]=12 | 10 _                                  # insert 12: hole created at index 2; 12 stored in index 0
  [0]=- | 10 12                                  # place 12 in index 2 (parent 10 is not larger)
  [0]=1 | 10 12 _                                # insert 1: hole created at index 3; 1 stored in index 0
  [0]=1 | _ 12 10                                # 1 < parent 10 (index 1) -> slide 10 down to index 3; hole moves to 1
  [0]=- | 1 12 10                                # place 1 in index 1 (hole is the root)
  [0]=14 | 1 12 10 _                             # insert 14: hole created at index 4; 14 stored in index 0
  [0]=- | 1 12 10 14                             # place 14 in index 4 (parent 12 is not larger)
  [0]=6 | 1 12 10 14 _                           # insert 6: hole created at index 5; 6 stored in index 0
  [0]=6 | 1 _ 10 14 12                           # 6 < parent 12 (index 2) -> slide 12 down to index 5; hole moves to 2
  [0]=- | 1 6 10 14 12                           # place 6 in index 2 (parent 1 is not larger)
  [0]=5 | 1 6 10 14 12 _                         # insert 5: hole created at index 6; 5 stored in index 0
  [0]=5 | 1 6 _ 14 12 10                         # 5 < parent 10 (index 3) -> slide 10 down to index 6; hole moves to 3
  [0]=- | 1 6 5 14 12 10                         # place 5 in index 3 (parent 1 is not larger)
  [0]=8 | 1 6 5 14 12 10 _                       # insert 8: hole created at index 7; 8 stored in index 0
  [0]=- | 1 6 5 14 12 10 8                       # place 8 in index 7 (parent 5 is not larger)
  [0]=15 | 1 6 5 14 12 10 8 _                    # insert 15: hole created at index 8; 15 stored in index 0
  [0]=- | 1 6 5 14 12 10 8 15                    # place 15 in index 8 (parent 14 is not larger)
  [0]=3 | 1 6 5 14 12 10 8 15 _                  # insert 3: hole created at index 9; 3 stored in index 0
  [0]=3 | 1 6 5 _ 12 10 8 15 14                  # 3 < parent 14 (index 4) -> slide 14 down to index 9; hole moves to 4
  [0]=3 | 1 _ 5 6 12 10 8 15 14                  # 3 < parent 6 (index 2) -> slide 6 down to index 4; hole moves to 2
  [0]=- | 1 3 5 6 12 10 8 15 14                  # place 3 in index 2 (parent 1 is not larger)
  [0]=9 | 1 3 5 6 12 10 8 15 14 _                # insert 9: hole created at index 10; 9 stored in index 0
  [0]=9 | 1 3 5 6 _ 10 8 15 14 12                # 9 < parent 12 (index 5) -> slide 12 down to index 10; hole moves to 5
  [0]=- | 1 3 5 6 9 10 8 15 14 12                # place 9 in index 5 (parent 3 is not larger)
  [0]=7 | 1 3 5 6 9 10 8 15 14 12 _              # insert 7: hole created at index 11; 7 stored in index 0
  [0]=7 | 1 3 5 6 _ 10 8 15 14 12 9              # 7 < parent 9 (index 5) -> slide 9 down to index 11; hole moves to 5
  [0]=- | 1 3 5 6 7 10 8 15 14 12 9              # place 7 in index 5 (parent 3 is not larger)
  [0]=4 | 1 3 5 6 7 10 8 15 14 12 9 _            # insert 4: hole created at index 12; 4 stored in index 0
  [0]=4 | 1 3 5 6 7 _ 8 15 14 12 9 10            # 4 < parent 10 (index 6) -> slide 10 down to index 12; hole moves to 6
  [0]=4 | 1 3 _ 6 7 5 8 15 14 12 9 10            # 4 < parent 5 (index 3) -> slide 5 down to index 6; hole moves to 3
  [0]=- | 1 3 4 6 7 5 8 15 14 12 9 10            # place 4 in index 3 (parent 1 is not larger)
  [0]=11 | 1 3 4 6 7 5 8 15 14 12 9 10 _         # insert 11: hole created at index 13; 11 stored in index 0
  [0]=- | 1 3 4 6 7 5 8 15 14 12 9 10 11         # place 11 in index 13 (parent 5 is not larger)
  [0]=13 | 1 3 4 6 7 5 8 15 14 12 9 10 11 _      # insert 13: hole created at index 14; 13 stored in index 0
  [0]=- | 1 3 4 6 7 5 8 15 14 12 9 10 11 13      # place 13 in index 14 (parent 8 is not larger)
  [0]=2 | 1 3 4 6 7 5 8 15 14 12 9 10 11 13 _    # insert 2: hole created at index 15; 2 stored in index 0
  [0]=2 | 1 3 4 6 7 5 _ 15 14 12 9 10 11 13 8    # 2 < parent 8 (index 7) -> slide 8 down to index 15; hole moves to 7
  [0]=2 | 1 3 _ 6 7 5 4 15 14 12 9 10 11 13 8    # 2 < parent 4 (index 3) -> slide 4 down to index 7; hole moves to 3
  [0]=- | 1 3 2 6 7 5 4 15 14 12 9 10 11 13 8    # place 2 in index 3 (parent 1 is not larger)

final heap (from index 1): 1,3,2,6,7,5,4,15,14,12,9,10,11,13,8
```


**6.2b** buildHeap on the same input:

```
$ python tools/study.py heap build 10,12,1,14,6,5,8,15,3,9,7,4,11,13,2
buildHeap (min-heap)

  [0]=- | 10 12 1 14 6 5 8 15 3 9 7 4 11 13 2    # start (size 15); percolateDown from i = 7 down to 1
  [0]=- | 10 12 1 14 6 5 2 15 3 9 7 4 11 13 8    # after percolateDown(7) (value 8)
  [0]=- | 10 12 1 14 6 4 2 15 3 9 7 5 11 13 8    # after percolateDown(6) (value 5)
  [0]=- | 10 12 1 14 6 4 2 15 3 9 7 5 11 13 8    # after percolateDown(5) (value 6)
  [0]=- | 10 12 1 3 6 4 2 15 14 9 7 5 11 13 8    # after percolateDown(4) (value 14)
  [0]=- | 10 12 1 3 6 4 2 15 14 9 7 5 11 13 8    # after percolateDown(3) (value 1)
  [0]=- | 10 3 1 12 6 4 2 15 14 9 7 5 11 13 8    # after percolateDown(2) (value 12)
  [0]=- | 1 3 2 12 6 4 8 15 14 9 7 5 11 13 10    # after percolateDown(1) (value 10)

final heap (from index 1): 1,3,2,12,6,4,8,15,14,9,7,5,11,13,10
```


**6.3** Three deleteMins on "the heap of the previous exercise" (it does not say which; the two heaps differ, so state which one you use):

```
$ python tools/study.py heap delete 1,3,2,6,7,5,4,15,14,12,9,10,11,13,8 --count 3
min-heap deleteMin x3 (removed [1, 2, 3])

  [0]=8 | _ 3 2 6 7 5 4 15 14 12 9 10 11 13      # deleteMin: remove 1 from the root (hole at 1); last element 8 goes to index 0; size 14
  [0]=8 | 2 3 _ 6 7 5 4 15 14 12 9 10 11 13      # smaller child 2 (index 3) beats 8 -> slide it up to index 1; hole moves to 3
  [0]=8 | 2 3 4 6 7 5 _ 15 14 12 9 10 11 13      # smaller child 4 (index 7) beats 8 -> slide it up to index 3; hole moves to 7
  [0]=8 | 2 3 4 6 7 5 _ 15 14 12 9 10 11 13      # best child 13 (index 14) does not beat 8 -> stop
  [0]=- | 2 3 4 6 7 5 8 15 14 12 9 10 11 13      # place 8 in index 7
  [0]=13 | _ 3 4 6 7 5 8 15 14 12 9 10 11        # deleteMin: remove 2 from the root (hole at 1); last element 13 goes to index 0; size 13
  [0]=13 | 3 _ 4 6 7 5 8 15 14 12 9 10 11        # smaller child 3 (index 2) beats 13 -> slide it up to index 1; hole moves to 2
  [0]=13 | 3 6 4 _ 7 5 8 15 14 12 9 10 11        # smaller child 6 (index 4) beats 13 -> slide it up to index 2; hole moves to 4
  [0]=13 | 3 6 4 _ 7 5 8 15 14 12 9 10 11        # best child 14 (index 9) does not beat 13 -> stop
  [0]=- | 3 6 4 13 7 5 8 15 14 12 9 10 11        # place 13 in index 4
  [0]=11 | _ 6 4 13 7 5 8 15 14 12 9 10          # deleteMin: remove 3 from the root (hole at 1); last element 11 goes to index 0; size 12
  [0]=11 | 4 6 _ 13 7 5 8 15 14 12 9 10          # smaller child 4 (index 3) beats 11 -> slide it up to index 1; hole moves to 3
  [0]=11 | 4 6 5 13 7 _ 8 15 14 12 9 10          # smaller child 5 (index 6) beats 11 -> slide it up to index 3; hole moves to 6
  [0]=11 | 4 6 5 13 7 10 8 15 14 12 9 _          # smaller child 10 (index 12) beats 11 -> slide it up to index 6; hole moves to 12
  [0]=- | 4 6 5 13 7 10 8 15 14 12 9 11          # place 11 in index 12

final heap (from index 1): 4,6,5,13,7,10,8,15,14,12,9,11
```


and on the buildHeap result of 6.2b:

```
$ python tools/study.py heap delete 1,3,2,12,6,4,8,15,14,9,7,5,11,13,10 --count 3
min-heap deleteMin x3 (removed [1, 2, 3])

  [0]=10 | _ 3 2 12 6 4 8 15 14 9 7 5 11 13      # deleteMin: remove 1 from the root (hole at 1); last element 10 goes to index 0; size 14
  [0]=10 | 2 3 _ 12 6 4 8 15 14 9 7 5 11 13      # smaller child 2 (index 3) beats 10 -> slide it up to index 1; hole moves to 3
  [0]=10 | 2 3 4 12 6 _ 8 15 14 9 7 5 11 13      # smaller child 4 (index 6) beats 10 -> slide it up to index 3; hole moves to 6
  [0]=10 | 2 3 4 12 6 5 8 15 14 9 7 _ 11 13      # smaller child 5 (index 12) beats 10 -> slide it up to index 6; hole moves to 12
  [0]=- | 2 3 4 12 6 5 8 15 14 9 7 10 11 13      # place 10 in index 12
  [0]=13 | _ 3 4 12 6 5 8 15 14 9 7 10 11        # deleteMin: remove 2 from the root (hole at 1); last element 13 goes to index 0; size 13
  [0]=13 | 3 _ 4 12 6 5 8 15 14 9 7 10 11        # smaller child 3 (index 2) beats 13 -> slide it up to index 1; hole moves to 2
  [0]=13 | 3 6 4 12 _ 5 8 15 14 9 7 10 11        # smaller child 6 (index 5) beats 13 -> slide it up to index 2; hole moves to 5
  [0]=13 | 3 6 4 12 7 5 8 15 14 9 _ 10 11        # smaller child 7 (index 11) beats 13 -> slide it up to index 5; hole moves to 11
  [0]=- | 3 6 4 12 7 5 8 15 14 9 13 10 11        # place 13 in index 11
  [0]=11 | _ 6 4 12 7 5 8 15 14 9 13 10          # deleteMin: remove 3 from the root (hole at 1); last element 11 goes to index 0; size 12
  [0]=11 | 4 6 _ 12 7 5 8 15 14 9 13 10          # smaller child 4 (index 3) beats 11 -> slide it up to index 1; hole moves to 3
  [0]=11 | 4 6 5 12 7 _ 8 15 14 9 13 10          # smaller child 5 (index 6) beats 11 -> slide it up to index 3; hole moves to 6
  [0]=11 | 4 6 5 12 7 10 8 15 14 9 13 _          # smaller child 10 (index 12) beats 11 -> slide it up to index 6; hole moves to 12
  [0]=- | 4 6 5 12 7 10 8 15 14 9 13 11          # place 11 in index 12

final heap (from index 1): 4,6,5,12,7,10,8,15,14,9,13,11
```


**6.4** The array for a **non-complete** tree must reach the highest index used; a node at depth d has an index up to 2^(d+1) - 1. A complete tree of N nodes has deepest depth floor(log N) and needs N cells.
(a) Two extra levels: deepest depth floor(log N) + 2, so the array needs up to 2^(floor(log N)+3) - 1 < **8N** cells.
(b) Deepest node at depth 2 log N: up to 2^(2 log N + 1) = **2N^2** cells. (c) Depth 4.1 log N: 2^(4.1 log N + 1) = **2 N^4.1** cells.
(d) Worst case: a chain (every node has one child) with depth N-1: **2^N - 1** cells (exponential).

**6.5** The book's Fig 6.8 *already* puts a copy of the item in position 0 (that is the version in section 3). The version without the copy needs an explicit `hole > 1` test:

```cpp
void insert( const Comparable & x )
{
    if( currentSize == array.size( ) - 1 )
        array.resize( array.size( ) * 2 );
    int hole = ++currentSize;
    for( ; hole > 1 && x < array[ hole / 2 ]; hole /= 2 )   // explicit root test replaces the sentinel
        array[ hole ] = array[ hole / 2 ];
    array[ hole ] = x;
}
```

**6.6** Figure 6.13 (a very large complete binary tree): count the levels: 1 + 2 + 4 + 8 + 16 + 32 + 64 = 127 nodes in the full levels (depths 0-6) plus 98 nodes in the last level
(depth 7, filled left to right) = **225 nodes**. (I counted the drawn circles in the book's figure: levels 1, 2, 4, 8, 16, 32, 64, 98.)

**6.7a** Prove buildHeap uses at most 2N - 2 comparisons. One loop iteration of `percolateDown` makes **2 comparisons** and moves the hole down one level, so `percolateDown(i)` makes **at most 2 height(i)** comparisons.
Total <= 2 x H, H = sum of heights of all nodes. **Lemma: H(N) = N - b(N) <= N - 1.** Proof: remove all the leaves of the complete tree; the remaining nodes (exactly the floor(N/2) internal nodes) form a complete tree
and **every internal node's height drops by exactly 1**, while the leaves contributed 0. So H(N) = H(floor(N/2)) + floor(N/2), i.e. H(N) = floor(N/2) + floor(N/4) + floor(N/8) + ... (this is the slides' N/2 + N/4 + ... series) which is **< N**. (Induction
gives N - b(N): if N = 2m then b(N) = b(m); if N = 2m+1 then b(N) = b(m)+1, and both agree with 2m - b(m).) Hence comparisons <= 2(N - 1) = **2N - 2**. For the 15-element tree (N = 15, b = 4): H = 11, at most 22 comparisons.

**6.8** (a) The maximum is at a leaf: if the maximum were at an internal node it would have a child >= it by heap order; that child also holds a maximum; repeat down the tree until a leaf.
(b) Exactly ceil(N/2) leaves ("N/2"): node i has a child iff 2i <= N, so the internal nodes are 1..floor(N/2), leaving N - floor(N/2) = ceil(N/2) leaves.
(c) Every leaf must be examined: if some leaf were skipped, replacing its key by a value larger than everything else still gives a valid heap (a leaf only needs to be >= its parent), so you cannot rule out that the skipped leaf is the max. So you need Omega(N), not "O(1) because the root is smallest".

**6.10a** Print all nodes < X in O(K) (K = number printed). Preorder traversal that **does not enter a subtree whose root is >= X** (everything below it is >= it, hence >= X):

```cpp
void printLessThan( int i, const Comparable & x ) const   // call with i = 1
{
    if( i > currentSize || !( array[ i ] < x ) )          // empty or >= x: prune the whole subtree
        return;
    std::cout << array[ i ] << ' ';
    printLessThan( 2 * i, x );
    printLessThan( 2 * i + 1, x );
}
```

Every call either prints a node (K of them) or returns immediately; the immediate returns are children of printed nodes (<= 2K) or the root: **at most 2K + 1 calls, O(K)**.
**6.10b** Yes: it works on any heap-ordered tree (leftist, skew, and each tree of a binomial queue; for a binomial queue add O(log N) to look at all the roots).
**6.10c** Find an arbitrary X using about 3N/4 comparisons. Only about N/4 nodes have height 1 (parents of leaves), N/2 are leaves, N/4 have height >= 2.
Algorithm: (1) for each node p of height 1, compare X with p. If X < p: stop looking below p (its leaf children are >= p > X) - cost 1. If X = p: found. If X > p: compare X with p's leaf children - cost at most 3 per height-1 node, **at most 3 x N/4 comparisons** in total.
(2) Every ancestor of a height-1 node p with p < X is <= p < X, so it cannot equal X: skip it without comparing. (3) The remaining high nodes (all of whose height-1 descendants satisfied X < p) are compared directly with X: each such node sits above height-1 nodes that cost only 1 instead of 3, which pays for it.
So the total is about 3N/4 in the worst case, versus N for a plain scan.

**6.18 (min-max heap)** (a) The minimum is the root; the maximum is the larger of the root's two children (depth-1 nodes are on a max level), or the root if N = 1: O(1).
(b) insert: add the new key x at the next leaf position; compare with its parent q. If x is on a **min** level and x > q (q is on a max level), swap them and then percolate x up along the **max** levels (compare with the grandparent, swap while x > grandparent); otherwise percolate up along the **min** levels (swap with the grandparent while x < grandparent). A node on a max level is handled symmetrically. O(log N).
(c) deleteMin: take the root out and move the last element x to the root; **trickle down**: let m = the smallest among the children and grandchildren. If m is a grandchild and m < x: swap x and m; if x is now larger than its new parent (a max-level node), swap them too; repeat from m's position. If m is a child and m < x: swap and stop. Otherwise stop. deleteMax is symmetric, starting from the larger child of the root. O(log N) (two levels per step).
(d) Yes, linear time: run the same trickle-down from i = N/2 down to 1 (using the min or max version according to the level of i); each costs O(height(i)), and the sum of heights is O(N) (Theorem 6.1).

**HW6 Q2** is the deleteMin trace in section 4.

**HW6 Q3/Q4** (LeetCode "Kth Largest Element in a Stream": the class stores `k` and a min-heap of the k largest values seen; `add(val)` returns the k-th largest). Q3 with `priority_queue<int, vector<int>, greater<int>>`: `add` pushes `val`, pops if size > k: two O(log k) operations every time.
**Q4: more efficient by manipulating the vector directly:** (1) build the initial heap with `make_heap` on the vector (O(n)) instead of n pushes (O(n log k)); (2) in `add`, when the heap is full and `val <= heap.front()` do **nothing** (O(1)); (3) otherwise overwrite the root (`heap[0] = val`) and percolate **down** once (about log k steps, half the work of pop + push; `std::pop_heap` + `back() = val` + `push_heap` is the library way and costs two log k steps). With `priority_queue` you cannot replace the top in place; the vector lets you do one percolateDown instead of a deleteMin + insert.

---

<!-- /HOLD -->

## 13. What the exam asks (and how to answer)

| Likely question | Answer shape |
|---|---|
| Insert / deleteMin / buildHeap trace (min or max) | Textbook layout; array from index 1; show index 0 and the hole after each step; give the final array. |
| "Is this array a heap?" | Compare each index i >= 2 with `i/2`; report the first violation. |
| Prove buildHeap is O(N) | Cost of percolateDown(i) <= height(i); sum of heights; geometric series or Theorem 6.1. |
| Average O(1) insert, when does it fail? | Constant expected rise for same-distribution inputs; fails for sorted-decreasing or alternating insert/deleteMin. |
| Where is the max / k-th smallest? | Max in a leaf (ceil(N/2) candidates). The k-th smallest is at depth <= k-1. |
| Design with a heap and analyze | Name each STL call's cost; loops multiply, steps add; e.g. top-k = O(N log k), merge k sorted lists = O(N log k). |
| Heap vs BST vs sorted list | Table in section 1. |
