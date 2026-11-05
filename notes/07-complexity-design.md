# 07 - Complexity Analysis and "Design + Analyze" Questions (cumulative: Ch 2-7 + every container in the semester)

> **Priority: highest. This is the single biggest block of Exam 2.** The topics page says complexity analysis
> (*"including questions that ask for design and analysis"*) and coding are **cumulative** and together are
> **about half the points, "more thorough than exam 1"**. The professor's own practice sheet has three questions:
> (1) analyze heapsort, (2) *k* inserts into a splay tree of size *n* (tight bound!), (3) the online-seminar design
> question ("what data structure(s) will you use and why? Describe and **fully analyze** the complexity"). Learn the
> *style* of those three answers. Everything below trains that style.

Sources: `exam2_Complexity_Analysis_Practice_Questions` (the gold standard), `exam2_Topics_and_Questions`, slides
*Associative Arrays and Hashing* ("Classic Hash Table Problem": naive / sorting / hashing), *C++ STL*, *Leetcode Hashing
Questions*, *Heaps*, *Sorting*; HW5 Part 3c (DNA sequences, `unordered_map` vs `map`), HW4 Q2 (`O(n log k)` with a `set`),
HW6 Q3-4 (k-th largest in a stream), Weiss 5.x, 6.4 (selection problem), 7.5-7.8; Exam 1 notes `03-algorithm-analysis.md`
and the HW1 Part C / HW2 `printLots` / HW4 solutions (the line-by-line justification style carries over).

## Conventions box (what the professor grades by)

* **A Big-O answer means the tight bound.** A loose bound ("heapsort is O(n^3)") gets no credit.
* **Justify every step**: name each operation, give its cost *and the reason*, then combine: **loops multiply,
  consecutive steps add (the largest wins)**. The professor writes things like *"a bunch of O(1) and O(log k) operations in
  sequence is O(log k), n times = O(n log k)"* (HW4 solution). Copy that rhythm.
* **Say which case you mean**: worst / average / amortized. For anything hash-based, *always* write "O(1) average, O(n) worst".
* **Use the right variables.** If the input has two sizes, the answer has two variables (`n` and `k`, `n` and `m`, `L` = string length).
  Do not collapse them unless you can justify it.
* **Name the cost of each library call you rely on**, as on cplusplus.com: `unordered_map` insert/find/erase average O(1), worst
  O(n); `set`/`map` O(log n); `priority_queue` push/pop O(log n), top O(1), range constructor / `make_heap` O(n);
  `vector::push_back` amortized O(1), middle insert/erase O(n); `list` insert/erase at an iterator O(1); `sort` O(n log n).
* **Design questions want WHY**: "unordered set because we only ask *is it in the collection*, many times, and need no order";
  "vector because we must remember insertion order and need random access". A correct structure with no reason loses points.
* **Answers must use the textbook version** of each algorithm (see the AI-use warning): buildHeap is the bottom-up
  `percolateDown` loop, `insert` percolates up, rehash doubles to the next prime, quicksort uses the textbook partition.

---

## 1. Start from a worked example: the seminar question, annotated

**Question (professor's practice question 3, paraphrased).** A file has millions of names (unsorted). When someone joins,
if their name is on the list they are admitted and their name is recorded in order of arrival; each name can be admitted only
once. At the end print every 100th guest in arrival order. About half the listed people attend. Choose data structures and
fully analyze the design. Let *n* = names in the file.

**Model answer, with my commentary in brackets.**

1. *Need:* "is this name on the list?", asked once per arrival. [Identify the repeated operation first.]
   *Choice:* `unordered_set<string>`. [Only membership and delete are needed: no order, no range. Hash gives O(1) average.]
2. *Load the list:* read *n* names sequentially, O(n); insert each into the hash, O(1) average each, O(n) total. [Note: reading
   the file and inserting are *both* linear and they add; they do not multiply.]
3. *Arrivals:* for each guest do one `find`/`erase` in the hash (O(1) average) - this also enforces "admitted once", because the
   name is gone after the first admission. About n/2 guests arrive -> O(n) total. [Removing from the set is how you
   get the "only once" rule for free.]
4. *Record order:* the order of arrival must be remembered, and a hash cannot do that, so push each admitted name onto the end
   of a `vector` with `push_back` (amortized O(1)) -> O(n) total.
5. *Prizes:* touch indices 99, 199, 299, ... of the vector. A vector has random access, so each is O(1); there are about
   (n/2)/100 of them -> O(n) at most. [The professor says "about n/100 accesses, but that's still O(n)". Do not try to be
   cleverer than needed: O(n/100) = O(n).]
6. *Total:* every step is O(n), the steps are consecutive, so **O(n) average**. [Because hashing is involved you should add:
   **worst case O(n^2)** if every name collides into one bucket - each hash operation degrades to O(n). Saying so shows you
   know the cost of hashing; the professor's own answer states the average-case figure.]

What made this a full-credit answer, in order: (a) **each step is one operation with a data structure chosen for it**,
(b) **a reason** for each choice, (c) **a cost per element and a count of elements**, (d) **a sum at the end**.

### The method, distilled (use it on every design question)

| Step | What you do | Example above |
|---|---|---|
| 1. List the operations | Write down every *operation the problem needs*, and how often each is done. | "is name on list?" (many); "remember arrival order" (n/2); "index 100th, 200th..." (n/200) |
| 2. Match each to the cheapest structure | Look up the cost table (section 2). Ask: do I need order? range? min/max? position? | membership -> hash; order -> vector; index -> vector |
| 3. Cost per call | Write "X is O(...) because ..." for every call. | `find`/`erase` O(1) average (hash), `push_back` amortized O(1) |
| 4. Multiply by the count | Operations x repetitions; note any variable that changes inside the loop (container size grows!). | n/2 arrivals x O(1) |
| 5. Add the steps | Consecutive steps add; the largest wins. | O(n)+O(n)+O(n)+O(n) = O(n) |
| 6. Qualify the case | Hash -> "average O(1), worst O(n)". Splay -> amortized. Quicksort/quickselect -> average vs worst. | seminar: average O(n) |
| 7. (If asked) show it is tight | Give the lower bound (section 5). | not asked here |

**Mini check.** The same question but the prizes go to the guests whose arrival *name is alphabetically first among each 100*.
What changes? <details><summary>Answer</summary>Now you need an order on names: a hash cannot give it. Either sort the
vector of n/2 admitted names O(n log n) (dominates, total O(n log n)), or keep a `set`/`map` instead of the vector
(insert O(log n) each -> O(n log n)). The total becomes O(n log n) because ordering is genuinely needed - the
"cheapest structure" changed because the *operation* changed.</details>

---

## 2. Master cost table: every structure in the semester (memorize; it is a source of free points)

"n" = number of elements currently stored. **Reasons are part of the answer**: write them.

### 2.1 Sequence containers and arrays

| Operation | `vector` | `list` (doubly linked) | `deque` | Reason |
|---|---|---|---|---|
| `v[i]`, `at(i)` | O(1) | not available (`next(it,i)` is O(i)) | O(1) | vector/deque are contiguous / block arrays: address arithmetic. List must walk links. |
| `front()`, `back()` | O(1) | O(1) | O(1) | |
| `push_back` | **amortized O(1)**, worst O(n) on a reallocation | O(1) | O(1) | vector doubles when full: n pushes cost < 3n total. |
| `push_front` | not available (would be O(n)) | O(1) | O(1) | vector would shift everything. |
| `insert`/`erase` at an iterator in the middle | **O(n)** (shift) | **O(1)** | O(n) | list changes a constant number of pointers; vector shifts the tail. |
| find a value (unsorted) | O(n) | O(n) | O(n) | must look at each element. |
| find in a **sorted** vector (`binary_search`, `lower_bound`) | **O(log n)** | O(n) (no random access: STL walks) | O(log n) | random access is what makes binary search work. |
| `sort` | O(n log n) (`std::sort`, introsort) | `list::sort` O(n log n) | O(n log n) | `std::sort` needs random access, so list has a member. |
| `clear`, copy construct, iterate all | O(n) | O(n) | O(n) | |
| `size`, `empty`, `begin`, `end` | O(1) | O(1) | O(1) | |
| `reserve`/`resize` | O(n) if it reallocates | | | |

Key traps: `v.erase(v.begin())` in a loop = O(n^2); `list` "insert at index i" costs O(i) to get there; `list::size()` is O(1) in C++11.

### 2.2 Ordered associative containers (`set`, `map`, `multiset`, `multimap` = balanced BST, typically red-black)

| Operation | Cost | Reason |
|---|---|---|
| `insert`, `erase(key)`, `find`, `count`, `operator[]` (map) | **O(log n)** worst case | balanced tree: height O(log n), one root-to-leaf path |
| `lower_bound`, `upper_bound` | **O(log n)** | same descent |
| `begin()`, `rbegin()` -> min / max | **O(1)** | leftmost / rightmost node (the container stores it) |
| `++it`, `--it` | amortized O(1), worst O(log n) | in-order successor |
| iterate whole container in sorted order | **O(n)** | n amortized-O(1) steps |
| iterate a **range** `[lower_bound(a), upper_bound(b))` | **O(log n + m)** where m = number of elements in the range | one descent to find the start, then m steps |
| `std::distance(it1, it2)` on set iterators | **O(m)** (bidirectional, not random access) | trap: *counting* a range is not O(log n) |
| `erase(iterator)` | amortized O(1) | no search needed |
| build from n elements | O(n log n) (O(n) if the input is already sorted) | n inserts |
| `clear` | O(n) | |

The same costs apply to a hand-written **AVL tree** (find/insert/delete **O(log n) worst case**, height <= ~1.44 log n, single
insertion needs at most 1 rotation, deletion up to O(log n)). A plain **BST** is O(log n) *average* on random data but O(n) worst
case (sorted input). A **B-tree** of order M: find/insert/delete O(log n) overall; the point is the number of *disk accesses*,
O(log_M n), because the nodes are large.

### 2.3 Splay trees (amortized!)

| | cost |
|---|---|
| one find / insert / delete, **worst case** | **O(n)** (a single operation can walk a long path) |
| any M operations from an empty tree, total | **O(M log n)** -> **O(log n) worst-case amortized** per operation |
| one operation, **average** (random input) | **O(log n)** |

Never write "splay worst case O(log n)". The three phrases are different guarantees (Exam 1 note 07).

### 2.4 Hash tables / `unordered_set` / `unordered_map` (Ch 5)

| Operation | Average | Worst | Reason |
|---|---|---|---|
| `insert`, `find`/`count`, `erase`, `operator[]` | **O(1)** | **O(n)** | compute `h(x)` O(1); a bounded load factor means O(1) expected collisions; worst case every key is in one bucket / probe cluster |
| a single insert that triggers a rehash | O(n) | O(n) | all n elements are re-inserted into a table about twice as large |
| insert, **amortized over a sequence** (rehash included) | **O(1)** | | rehash cost 1+2+4+... doubles, sum < 2n over n inserts (proof in section 6) |
| iterate all elements | O(n) | O(n) | (if the table keeps a bounded load factor: O(n + TableSize) = O(n)) |
| min / max / sorted order / range query | **O(n) / not supported** | | a hash is unordered; slides: "O(1) insert, delete and lookup. And nothing else." |
| build from n elements | O(n) | O(n^2) | n inserts |
| `string` keys of length L | O(L) per op | O(nL) | hashing and comparing the key reads its characters |

Load-factor facts you may need: chaining rehash when lambda > 1 (table of chains tolerates lambda up to about 1); probing
needs lambda <= 0.5 (rehash at > 0.5); expected probes for linear probing grow like 1/(1-lambda)^2 for insertions, so the
bound is O(1) only while lambda stays bounded away from 1 (Weiss 5.4-5.5).

### 2.5 Binary heap / `priority_queue` (Ch 6)

| Operation | Cost | Reason |
|---|---|---|
| `top()` / findMin | **O(1)** | root |
| `push` / `insert` | **O(log n) worst, O(1) average** (random values) | place at the end O(1), percolate up <= height = log n; on average a random value moves up O(1) levels (slide proof). The O(1) average does *not* hold if you alternate insert with deleteMin. |
| `pop` / `deleteMin` | **O(log n) worst and average** | move last element to root, percolate down <= height |
| `buildHeap` / `make_heap` / range constructor | **O(n)** | percolateDown from n/2 to 1: sum of heights = n; *not* n log n |
| n inserts (one at a time) | O(n log n) worst, O(n) average | |
| `decreaseKey`, `increaseKey`, `remove` (given the position) | O(log n) | percolate one way; **finding** the position is O(n) in a heap |
| find an arbitrary value / find max in a min-heap | O(n) | heap order says nothing about siblings |
| `heapsort` | O(n log n) worst and average, O(1) extra space, not stable | buildHeap O(n) + n deleteMax x O(log n) |
| k-th smallest by `buildHeap` + k `deleteMin` | O(n + k log n) | |
| k-th smallest/largest by a size-k heap | O(n log k) time, O(k) space | n pushes/pops on a heap of size k |
| merge two heaps of sizes n, m | O(n + m) (concatenate and buildHeap) | |

### 2.6 Sorting-related (Ch 7) - needed whenever a design says "sort first"

| Routine | Cost | Notes |
|---|---|---|
| merge of two sorted sequences (sizes a, b) | **O(a + b)**, O(a+b) extra space | one pass, each comparison outputs one element |
| mergesort | O(n log n) best/avg/worst, O(n) extra space, stable | T(n)=2T(n/2)+O(n) |
| partition (quicksort / quickselect) | **O(n)** | one sweep with i and j |
| quicksort | **O(n log n) average, O(n^2) worst** | median-of-3 avoids sorted-input worst case but not all |
| quickselect | **O(n) average, O(n^2) worst** | T(n)=T(n/2)+O(n) = O(n) (one side only) |
| heapsort | O(n log n) all cases, in place | |
| introsort (`std::sort`) | **O(n log n) worst** | quicksort until depth ~2 log n, then heapsort; insertion sort for tiny ranges |
| insertion sort | O(n^2) worst/avg, O(n) if nearly sorted, O(n + I) with I inversions | |
| counting sort (light) | O(n + K) for integer keys in range K | needs a known small range |
| any comparison sort | **Omega(n log n)** worst | decision tree has n! leaves, depth >= ceil(log n!) |
| `std::nth_element` | O(n) average | library quickselect |

### 2.7 One-line "which structure answers which question" (cheapest known)

| I need to... | Use | Cost |
|---|---|---|
| ask "have I seen x?" many times, no order | `unordered_set` | O(1) avg |
| count occurrences by key | `unordered_map<K,int>` with `m[k]++` | O(1) avg per item |
| remember insertion order | `vector` + `push_back` | amortized O(1) |
| repeatedly take the smallest/largest | `priority_queue` | O(log n) per pop |
| smallest/largest **and** delete arbitrary / update / range | `set`/`map`/`multiset` | O(log n) |
| range query `[a,b]`, predecessor/successor | `set` + `lower_bound`, or sorted `vector` + `lower_bound` | O(log n) (+ m to list) |
| static data, many lookups | sorted `vector` + binary search | O(n log n) once, O(log n) per query |
| frequent insert/delete in the *middle given an iterator* | `list` | O(1) |
| k-th smallest once | quickselect (`nth_element`) | O(n) avg |

**Mini check.** Why is `std::set::lower_bound` O(log n) but `std::lower_bound(s.begin(), s.end(), x)` on a `set` O(n)?
<details><summary>Answer</summary>The member function searches the tree. The generic algorithm uses only the iterator interface;
set iterators are bidirectional, so advancing by half of the range costs O(n) steps (it still makes O(log n) comparisons but
O(n) iterator moves). On a `vector` the iterator is random access, so the generic version is O(log n).</details>

### 2.8 The textbook routines, costed line by line (practice question 1 is built from these)

Weiss Fig 6.8 / 6.12 / 6.14 (binary heap, index 0 holds the value being moved, root at 1):

```cpp
void insert( const Comparable & x )                      // cost
{
    if( currentSize == array.size( ) - 1 )
        array.resize( array.size( ) * 2 );               // O(n) but only when full: doubling -> amortized O(1)
    int hole = ++currentSize;                            // O(1)
    Comparable copy = x;  array[ 0 ] = std::move( copy );// O(1)
    for( ; x < array[ hole / 2 ]; hole /= 2 )            // at most log n iterations (height); average O(1) iterations
        array[ hole ] = std::move( array[ hole / 2 ] );  //   O(1) per iteration: slide the parent down
    array[ hole ] = std::move( array[ 0 ] );             // O(1)
}                                                        // insert: O(log n) worst, O(1) average

void deleteMin( )
{
    array[ 1 ] = std::move( array[ currentSize-- ] );    // O(1): last element becomes the root candidate
    percolateDown( 1 );                                  // <= log n iterations of O(1): O(log n) worst AND average
}

void percolateDown( int hole )
{
    int child;  Comparable tmp = std::move( array[ hole ] );
    for( ; hole * 2 <= currentSize; hole = child )       // each iteration goes one level down: <= height = floor(log n)
    {
        child = hole * 2;
        if( child != currentSize && array[ child + 1 ] < array[ child ] ) ++child;   // pick smaller child: 1 comparison
        if( array[ child ] < tmp ) array[ hole ] = std::move( array[ child ] );      // 1 comparison, O(1) move
        else break;
    }
    array[ hole ] = std::move( tmp );
}

void buildHeap( )
{
    for( int i = currentSize / 2; i > 0; --i )           // n/2 calls ...
        percolateDown( i );                              // ... but a call at height h costs O(h): sum of heights = O(n)
}
```

Why buildHeap is Theta(n) and not n log n: a node at height h can move down at most h levels; a complete tree has at most
about n/2^(h+1) nodes of height h, so the work is sum over h of h * n/2^(h+1) = n * (sum h/2^(h+1)) = n (heap slide: 0*n/2 + 1*n/4 + 2*n/8 + ... = n).
Counting the same loop as "n/2 calls x log n" is a correct upper bound but **not tight**.

Heapsort (Fig 7.10) costed - this is the professor's practice question 1:

```cpp
for( int i = a.size( ) / 2 - 1; i >= 0; --i )   // buildHeap on a MAX-heap: O(n)
    percDown( a, i, a.size( ) );
for( int j = a.size( ) - 1; j > 0; --j )        // n-1 iterations
{
    std::swap( a[ 0 ], a[ j ] );                // O(1): max goes to its final place, heap shrinks to j elements
    percDown( a, 0, j );                        // O(log j) <= O(log n)
}                                               // phase 2: sum of log j = O(n log n)
```
Total O(n) + O(n log n) = **O(n log n)**, same for best/worst/average, **O(1) extra space**, not stable. (Tight: it sorts by comparisons, so
Omega(n log n) by the decision-tree theorem; or: the first n/2 iterations each percolate Omega(log n).)

**Mini check.** Insert n values one at a time into an initially empty min-heap: worst-case total? average total? Versus buildHeap?
<details><summary>Answer</summary>Worst: the i-th insert may rise log i levels: sum log i = O(n log n) (tight: decreasing values - see the engine example in section 5). Average
(random values): each insert O(1), total O(n). buildHeap: O(n) *worst case* on any input. So buildHeap is at least as good, and strictly better in the worst case.</details>

---

## 3. Analyzing code with library calls inside loops

**Recipe.** (1) Annotate every statement with its cost; (2) for every loop write *iterations x cost of one iteration*;
(3) if the container **changes size** inside the loop, bound its size by the largest it gets (or sum if the size grows
linearly); (4) add the pieces; (5) say average vs worst for hash calls.

### Worked example A: a `set` inside a loop gives n log n

```cpp
set<int> s;
for (int i = 0; i < n; ++i)      // n iterations
    s.insert(v[i]);              // O(log |s|) <= O(log n)
```
`insert` is O(log n) (balanced BST); n of them: **O(n log n)**. Tight: half the inserts go into a set of size >= n/2 (if the
elements are distinct), each costing Omega(log(n/2)) = Omega(log n).
With an `unordered_set`, the same loop is O(n) average, O(n^2) worst.

### Worked example B: the loop that *looks* O(n) but is O(n^2)

```cpp
vector<int> v;                   // size n
for (int i = 0; i < n; ++i)
    v.insert(v.begin(), i);      // O(current size) -- shifts everything right
```
Insert at the front of a vector shifts all `i` elements: 0+1+...+(n-1) = n(n-1)/2 = **O(n^2)**. With `list::push_front`
it would be O(1) each, O(n) total. With a `deque`, also O(n).

### Worked example C: the hash `operator[]` trap

```cpp
unordered_map<int,int> m;
for (int x : a)                  // n items
    if (m[x] == 0) m[x] = 1;     // two lookups, and the first one CREATES the entry
```
Each `m[x]` is O(1) average, O(size) worst, so the loop is **O(n) average, O(n^2) worst**. The second trap: `m[y]` used just
to *test* y inserts a default-constructed entry for y, so the map keeps growing (the HW5 handout warns that `myMap[x]` can't be used
to check membership - use `find` or `count`).

### Worked example D: nested loops with a growing container

```cpp
map<pair<int,int>,int> m;
for (int i = 0; i < n; ++i)
    for (int j = 0; j < n; ++j)
        m[{i, j}] = i * j;       // map has up to n^2 entries
```
n^2 iterations, each an O(log(size)) map access with size <= n^2. log(n^2) = 2 log n = O(log n), so **O(n^2 log n)**.
(Comparing a pair key is O(1).) With `unordered_map<long long,int>`, O(n^2) average.

### Worked example E: priority queue drained and refilled

```cpp
int lastStone(vector<int>& s) {
    priority_queue<int> pq(s.begin(), s.end());   // range constructor = make_heap: O(n)
    while (pq.size() > 1) {
        int a = pq.top(); pq.pop();               // top O(1); pop O(log n)
        int b = pq.top(); pq.pop();               // O(log n)
        if (a != b) pq.push(a - b);               // O(log n)
    }
    return pq.empty() ? 0 : pq.top();
}
```
Every iteration removes two elements and adds at most one, so the size drops by >= 1 and there are at most n-1 iterations.
Each iteration is three O(log n) operations -> O(log n). Total **O(n) + (n-1) x O(log n) = O(n log n)**. Tight: when no two
stones are equal the loop runs n-1 times with heap sizes n, n-1, ..., 2, and half of those iterations have size >= n/2.

### Worked example F: strings as keys

```cpp
unordered_map<string,int> freq;
for (const string& w : words)    // n words, each at most L characters
    ++freq[w];
```
Hashing a string reads all its characters: O(L). A bucket comparison is also O(L). So each access is **O(L) average** and the
loop is **O(nL) average**; worst case every word collides and each lookup compares against up to n keys: O(n L) per
access, **O(n^2 L)**. The HW5 solution (DNA substrings of length 10) calls this an "expensive O(1)": when L is a fixed
constant (10), O(L) = O(1) and the total is O(n). *State which one you are assuming.*

### Traps (each of these has cost people points)

* **Hidden size growth**: the cost of a `set` insert depends on the size *at that moment*; use the final size as the bound,
  and justify tightness by the "half the insertions" trick (section 5).
* **Hidden copies**: passing `vector<int>` by value in a loop adds O(n) per call; `string::substr` is O(length of the
  substring); building a `set` from a vector inside a loop is O(n log n) per iteration.
* **`std::distance`/`std::advance` on a list or set** is O(k), on a vector O(1).
* **`erase(value)` on a `multiset`** removes *all* copies; to remove one copy erase by iterator (`erase(ms.find(x))`).
* **`map::operator[]` and `unordered_map::operator[]` insert** when the key is missing.
* **Iterating an `unordered_map`** is O(n) but the order is unspecified; it cannot give a sorted answer.
* **An O(1) average hash cost is not a worst-case guarantee**; a design whose requirement says "guaranteed" or "worst case"
  needs a balanced tree or sorting.
* **A heap's `top()` is O(1), but finding the *k-th* element inside it is not** (position does not mean rank).

**Mini check.** What is the cost of `for (int i=0;i<n;++i) { vector<int> c(v); c.push_back(i); }`
(with |v| = n)? <details><summary>Answer</summary>The copy constructor is O(n), push_back amortized O(1) (but here one reallocation
is possible - the copy has capacity n, so push_back reallocates: O(n)). Each iteration is O(n), n iterations: **O(n^2)**.</details>

---

## 4. Several variables: n, k, m, L, and what to do with log(n+k)

Two or more independent sizes are common: "a list of *k* elements are inserted into a structure of size *n*", "merge *k*
sorted lists with *N* elements in total", "two arrays of sizes *n* and *m*", "*n* words of length *L*". Rules:

1. **Keep each variable.** O(n + k) is not O(n) unless you know k <= n (up to a constant). Never drop a variable silently.
2. **Sizes change while you work.** Practice question 2: inserting *k* items into a tree that starts at size *n* means the
   tree has size between *n* and *n+k*, so one insertion costs O(log(n+k)) - **not** O(log n). Total **O(k log(n+k))**.
3. **You may simplify only with a stated relation.**
   * If k <= n: log(n+k) <= log(2n) = O(log n), so O(k log n).
   * If k = n^2 (any polynomial relation): log(n + n^2) = O(log n), so O(k log n) still.
   * If k >= n: log(n+k) = O(log k), so O(k log k).
   * If k = 2^n: log(n+k) = Theta(n), so O(k n). No simplification to log n.
   Without a relation, **leave it as log(n+k)**: that is exactly what the professor wrote.
4. **Dominance with two variables**: O(n + k log n) cannot be reduced unless a relation is given; O(n log k) and O(k log n)
   are different functions.

### n log k versus k log n (they appear in selection and merging)

| Algorithm | Time | Why |
|---|---|---|
| keep a **size-k** heap while scanning *n* items (6B) | **O(n log k)** | n pushes/pops on a heap whose size never exceeds k: each is O(log k) |
| build a heap of all *n* then *k* `deleteMin` (6A) | **O(n + k log n)** | buildHeap O(n), k pops each O(log n) |
| merge *k* sorted lists with *N* total elements with a size-k heap | **O(N log k)** | N pop+push pairs on a heap of size k |
| repeatedly merge lists two at a time left to right | O(kN) | the accumulated list grows; each merge reads it again |
| sort everything | O(n log n) | |

Comparing 6A and 6B for the k-th smallest of *n*: if k is a constant, both are O(n); if k = n/2 (the median) both are
Theta(n log n); if k is about n / log n, 6A is O(n + (n/log n) log n) = O(n) while 6B is O(n log(n/log n)) = O(n log n), so 6A wins for
small k. 6B wins on space (O(k) instead of O(n)) and when the data arrives as a stream and cannot be stored. Quickselect is
O(n) *average for every k* (Sorting slides: "average case better than heap-based algorithms; median with heaps is O(n log n)").

### Worked example G (practice question 2, in the professor's style)

**Q.** A list of *k* elements is inserted into a splay tree of size *n*. Give the time for an average input as a tight bound.

**A.** Average-case insertion into a splay tree is O(log N) when the tree has N nodes. The tree does not stay at size n: the
j-th insertion goes into a tree of size n+j-1 <= n+k, so each costs O(log(n+k)). There are k insertions, so the total is
**O(k log(n+k))**.

**Tight:** half of the insertions (the last k/2) go into a tree of size at least n + k/2, so each costs at least about
log(n + k/2) on average; k/2 x log(n+k/2) = Omega(k log(n+k)) after ignoring constants (log(n+k/2) >= log((n+k)/2) = log(n+k) - 1).
Upper and lower bounds match, so the bound is tight.

*Why not "amortized"?* The question says "for an average input", so use the average-case per-insertion cost. If it had said
"worst-case amortized" the answer would be the same formula, O(k log(n+k)), but justified by the amortized bound - **and** the
bound would then hold for the whole sequence, not each insertion. If it asked the worst case of a *single* insertion, it is O(n+k).

---

## 5. How to argue that a bound is TIGHT (the half-the-operations trick)

Upper bound: "each of the k operations costs at most f, so the total is at most k f".
Lower bound (to show the upper bound cannot be improved): you cannot say "each costs f" because **early operations are cheaper**
(the structure is smaller). Instead:

> **Take the second half of the operations. Every one of them runs on a structure of size at least S/2 (S = final size), so
> each costs at least g(S/2). There are at least k/2 of them, so the total is at least (k/2) g(S/2), and g(S/2) is Theta(g(S))
> for logarithmic and polynomial g.**

The professor's wording (practice question 2): *"half of the insertions will be into a tree of at least size (n + k/2). So k/2
insertions will take an average of at least log(n + k/2) time. Ignoring all constants, this is also Omega(k log(n+k))."*

Templates:

| Situation | Upper bound | Tightness argument |
|---|---|---|
| n inserts into an empty AVL/BST/set | O(n log n) | last n/2 inserts are into size >= n/2: >= (n/2) log(n/2) = Omega(n log n). Equivalently sum log i = log(n!) = Theta(n log n). |
| n `deleteMin` from a heap of n (heapsort phase 2) | O(n log n) | first n/2 deleteMins happen while the heap has >= n/2 elements, each Omega(log n) percolate-down (the element moved to the root is a leaf value and usually sinks to the bottom): Omega(n log n). Also: it sorts, so by the decision-tree theorem it cannot beat Omega(n log n) comparisons. |
| k inserts into a heap of size n, worst-case input | O(k log(n+k)) | adversary inserts decreasing values: each percolates to the root. Second-half inserts see size >= n + k/2: Omega(k log(n+k)). *Engine check:* inserting 9,8,...,1 into a min-heap, every new value rises all the way to index 1 (`python tools/study.py heap insert "" "9,8,7,6,5,4,3,2,1"`). |
| k inserts into a hash table of size n, worst case (all keys collide) | O(k(n+k)) | the second half of the inserts each probe/scan >= n + k/2 entries: Omega(k(n+k)). *Engine check:* keys 10,20,30,40,50 with TableSize 10 all land in bucket 0 (one list of 5, or probes 0..4 for linear probing): `python tools/study.py hash run 10,20,30,40,50 --size 10 --method chain` / `linear`. |
| loop with a log-cost call in each iteration | O(n log n) | at least n/2 iterations see a size >= n/2 |
| nested loop `for i<n: for j<i:` with an O(1) body | O(n^2) | sum = n(n-1)/2; or: the last n/2 values of i each do >= n/2 iterations -> >= n^2/4 |

Also tight vs. loose: **a bound is *not* tight if some step has a lower cost that the sum hides.** Example: buildHeap is
O(n log n) by the naive count (n percolateDowns x log n) but that bound is *not tight*; the real bound is Theta(n) (the heap
slide: 0*n/2 + 1*n/4 + 2*n/8 + ... = n). Always prefer the proven tighter one.

**Mini check.** n inserts into an initially empty `std::set` cost O(n log n). Give the tightness argument in two lines.
<details><summary>Answer</summary>The last n/2 inserts go into a set of size at least n/2 (when keys are distinct). In a balanced tree
with s nodes every null link (where the new key is attached) is at depth Omega(log s), so an insertion into a set of size >= n/2 costs
Omega(log(n/2)) = Omega(log n). So the total is >=
(n/2) log(n/2) = Omega(n log n); with the upper bound this gives Theta(n log n).</details>

---

## 6. Average vs worst vs amortized: say which, and say why

| Guarantee | Meaning | Typical examples |
|---|---|---|
| **Worst case** (per operation) | the most any one operation can cost on any input | AVL ops O(log n); heap deleteMin O(log n); hash ops O(n); quicksort O(n^2) |
| **Average case** | expected cost over a *distribution of inputs* (random keys, random hash) | hash ops O(1); heap insert O(1) (random values); quicksort O(n log n); quickselect O(n); BST ops on random keys O(log n) |
| **Amortized** | cost of any sequence of M operations divided by M, *worst* sequence - no probability | `vector::push_back` O(1); hash insert including rehashes O(1)*; splay ops O(log n) |

*the "O(1) amortized hash insert" is on top of the average-case hashing assumption: the rehash cost is spread out, but individual collisions are still an average-case effect.

### Proof sketch: doubling gives amortized O(1) (vector growth and hash rehash)

* **Vector.** n `push_back` calls starting from capacity 1, doubling each time it is full: the reallocations happen at sizes
  1, 2, 4, ..., 2^j < n and copy that many elements: 1 + 2 + 4 + ... + 2^j < 2n. Plus n writes: **< 3n = O(n) for n pushes, so
  O(1) amortized**. (If the capacity grew by a *constant amount* c, there would be n/c reallocations copying about n each time: O(n^2/c), so
  O(n) amortized: the growth has to be a *factor*.)
* **Hash table (rehash by doubling).** The table is rehashed when load factor passes the threshold (chaining: lambda > 1,
  probing: > 0.5), moving to the next prime >= 2x the size. A rehash with m elements costs O(m) (re-hash each, O(1) each average)
  plus O(TableSize) to allocate/scan, which is also O(m) because lambda is at least about 1/4 right after a rehash. After a rehash
  the table has room for about as many new insertions as it has elements, so the next rehash happens at least m more
  insertions later, with cost about 2m. The rehash costs form 1 + 2 + 4 + ... < 2n over n insertions: **O(1) amortized per insertion, on top of the O(1) average cost of
  the insertion itself.**
* **Consequence for "k inserts into a hash of size n":** the k inserts cost O(k) *average* if we charge rehashes to the
  insertions that filled the table; strictly, a single rehash can cost O(n + k), so the total for this one batch is O(k) when no
  rehash falls inside it or when k >= n, and O(n+k) if one does. Say "O(k) average, plus O(n+k) if a rehash is triggered (amortized against earlier inserts)".

### Heap insert: average O(1) is fragile

Average O(1) needs the new values to come from the same distribution as the values already in the heap (heap slide). Alternating
`push` and `pop` breaks the assumption (pops remove the best elements, so new values percolate higher than average). In a design that interleaves, **use O(log n) per heap
operation**; do not claim O(1).

### Splay tree

State all three if asked: single op worst O(n); worst-case amortized O(log n) (M ops cost O(M log n) total); average O(log n).
For "k inserts into a splay tree of size n": total O(k log(n+k)) (worst-case amortized or average input).

### Quicksort and quickselect

Average O(n log n) / O(n) assumes the pivot splits "reasonably often"; worst case O(n^2) when the pivot is always the min or max
(sorted input with first-element pivot; median-of-3 fixes sorted input but not every adversary). If the problem demands a *guarantee* choose heapsort / mergesort / `std::sort` (introsort, O(n log n) worst).

---

## 7. Hash-based algorithms: how to analyze them

1. **Count hash operations** (insert / find / erase / `[]`) and give each O(1) average (O(L) if the key is a string of length L).
2. **Add the non-hash work** (reading the input O(n), scanning the table O(n) if the load factor is bounded, pushing to vectors).
3. **State both**: "O(n) average; O(n^2) worst if all keys collide."
4. **Space**: the hash holds up to u distinct keys: O(u) space - often the price paid for the speedup. Mention it.
5. **Rehash**: mention it is amortized into the O(1).
6. **When the problem asks for a guarantee** (hard real-time, adversarial input), compare with the balanced-BST version: O(n log n)
   *worst case* from `set`/`map`, no worst-case surprise.

Tools you use over and over (the Leetcode hashing slides):

| Pattern | Structure | Cost |
|---|---|---|
| contains duplicate | `unordered_set`: `if (!seen.insert(x).second) return true;` | O(n) avg |
| two sum / any pair sums to x | `unordered_set` or `unordered_map` value->index; look up `x - a[i]` *before* inserting a[i] | O(n) avg |
| count occurrences, valid anagram | `unordered_map<char,int>` or 26-array | O(n) |
| last position of each item (longest substring without repeats; contains duplicate II) | `unordered_map<item,int> last` | O(n) avg |
| sliding window of size k with membership | `unordered_set` window, insert new, erase `a[i-k]` | O(n) avg |
| repeated fixed-length substrings | `unordered_map<string,int>` with `substr` | O(nL) |
| intersection of two arrays | hash the smaller, scan the larger | O(n+m) avg |
| group by a canonical key (anagrams) | `unordered_map<key, vector<item>>` | O(total key-building cost) avg |

### Sorting first, or hashing? (the "Classic Hash Table Problem")

The slides ask for **naive, sorting, and hashing** solutions to "do any 2 integers in the array add to x?". The three-way comparison is
a standard exam shape:

| | Time | Extra space | Guarantee |
|---|---|---|---|
| naive: test all pairs | O(n^2) | O(1) | worst = best |
| sort + two pointers (or binary search per element) | O(n log n) | O(1) with an in-place sort | worst case O(n log n) |
| hash set | O(n) average, O(n^2) worst | O(n) | average only |

**When sorting helps**: (a) a *worst-case guarantee* is needed; (b) memory is tight; (c) the problem needs the data in order anyway
(range, neighbours, k-th, merge, "closest pair"); (d) the keys cannot be hashed. **When hashing helps**: membership / counting / grouping with
no order and a large n. Sorting by itself costs O(n log n) < O(n^2), so "sort first" is the standard way to beat a naive double loop
when you do not want hash space. If you sort and also need original indices, sort (value, index) pairs.

**Mini check.** Why is "sort + two pointers" correct and O(n) after sorting? <details><summary>Answer</summary>Put i at the smallest
and j at the largest. If a[i]+a[j] < x, then a[i] with any element <= a[j] is too small, so a[i] can't be part of any answer:
advance i. If > x, a[j] is too big with any element >= a[i]: decrease j. Each step permanently discards one index, so at most n-1 steps: O(n).
Total O(n log n) + O(n) = O(n log n).</details>

---

## 8. Worked design problems (write answers like these on the exam)

Each answer follows: **operations needed -> structure and why -> cost of each step -> total -> case/space -> (alternative).**

### Design 1 - Any two numbers that sum to x (slide "Classic Hash Table Problem")

*Given an integer array of size n, decide whether any two (different) elements add up to x.*

* **Naive.** Two nested loops over all pairs i < j: n(n-1)/2 comparisons of O(1) each -> **O(n^2) time, O(1) space.**
* **Sorting.** `sort` the array: O(n log n) (introsort, worst case). Then scan with two pointers, i from the left and j from the
  right: each step moves one pointer, at most n-1 steps -> O(n). Total O(n log n) + O(n) = **O(n log n) worst case, O(1) extra space** (the sort is in
  place). (Alternative: for each a[i], `binary_search` for x - a[i]: n x O(log n) = also O(n log n).)
* **Hashing.** `unordered_set<int> seen`. For each element a: if `seen.count(x - a)` return true; then `seen.insert(a)`. (Checking
  before inserting stops an element from pairing with itself.) n iterations x (one find O(1) average + one insert O(1) average) =
  **O(n) average**, **O(n^2) worst case** (all in one bucket), **O(n) space**.
* **Which is best?** Hashing is the fastest on average and is what we'd use; sorting is the best when we need a worst-case
  guarantee or must save memory.

### Design 2 - Deduplicate a stream, keeping first-seen order

*n items arrive; output each distinct item once, in order of first appearance.*

* Needed: (1) "seen before?" (2) preserve order of first appearance.
* (1) `unordered_set<T> seen`: `seen.insert(x)` returns `pair<iterator,bool>`; `.second` is true only if x was new -> O(1) average.
  (2) `vector<T> out`: if new, `out.push_back(x)` -> amortized O(1).
* Cost: n items x O(1) average = **O(n) average**, O(n^2) worst; space O(u) for u distinct. Using a `set` instead gives O(n log u)
  worst-case guaranteed. Sorting first (sort + `unique`) is O(n log n) and loses the original order unless you sort (value, index) pairs
  and re-sort by index: O(n log n), more complex than the hash.

### Design 3 - Top-k most frequent words

*n words, u distinct. Return the k most frequent.*

1. Count: `unordered_map<string,int>`, `++cnt[w]` per word: **O(n) average** (O(nL) if strings of length L).
2. Select the k largest of the u counts. Options:
   * sort all u pairs by count: O(u log u);
   * **size-k min-heap**: for each of the u pairs push; if size > k pop the smallest: u x O(log k) = **O(u log k)**; O(k) space;
   * `make_heap` the u pairs O(u) + k pops O(k log u) = **O(u + k log u)**;
   * `nth_element` (quickselect) O(u) average.
3. Total (size-k heap): **O(n + u log k)** average. Since u <= n this is within O(n log k). With sorting: O(n + u log u).
Pick the heap when k << u. All hash costs are averages (worst case O(n^2) for the counting).

### Design 4 - Leaderboard with updates

*Players have an id and a score. Operations: `setScore(id, s)` (many), `top(k)` (some), `scoreOf(id)` (many).*

* `unordered_map<int,int> score` (id -> score): `scoreOf` O(1) average and lets an update find the *old* score.
* `set<pair<int,int>> board` ordered by (score, id): `setScore` = look up old score in the hash O(1) avg; `board.erase({old,id})` O(log n);
  `board.insert({s,id})` O(log n); hash update O(1) -> **O(log n) per update**.
* `top(k)`: walk from `board.rbegin()` k steps: begin/rbegin O(1), k increments amortized O(1) each -> **O(k)**.
* A heap can't be used for the board: finding the old entry costs O(n) (or use lazy deletion with a counter and O(log n)).
* q updates: O(q log n) worst for the tree part + O(q) average for the hash. (A rank query "what position am I?" would need
  `std::distance(board.begin(), it)` = O(n): the STL has no order-statistics tree.)

### Design 5 - Merge k sorted arrays (N elements in total)

* **Plan A (repeated merge):** merge array 1 with 2, then the result with 3, ...: the accumulated array has size up to N, merged k-1 times:
  O(kN) worst.
* **Plan B (concatenate and sort):** O(N log N).
* **Plan C (heap of k):** `priority_queue` (min-heap) of (value, array id, position) with one entry per array: building it O(k); then repeat N times:
  `top`/`pop` O(log k), output, `push` the next element of that array O(log k) -> **O(k + N log k) = O(N log k)** since N >= k
  (assuming no empty arrays). Space O(k) beyond the output. Tight: sorted output of N values via comparisons of a k-way
  merge needs Omega(N log k) in general. (k = 2 gives the standard O(N) merge.)

### Design 6 - k-th smallest of n numbers (compare four ways)

| Method | Time | Space | Notes |
|---|---|---|---|
| sort, take a[k-1] | O(n log n) | O(1)-O(n) | simplest, ignores that we need only one element |
| `make_heap` + k `pop`s (6A) | **O(n + k log n)** | O(n) (copy) | best for small k; O(n log n) for k about n/2 |
| size-k max-heap while scanning (6B) | **O(n log k)** | O(k) | works on a stream; HW6 "k-th largest in a stream" |
| quickselect | **O(n) average**, O(n^2) worst | O(1) | median of three helps; use for the median |

> *A worked HW6 answer goes here. It is added to the public version after HW6 is due (Nov 10).*

### Design 7 - Sliding-window maximum (window w, n items)

* Naive: scan every window: O(nw).
* `multiset<int> win`: insert the new element O(log w), erase the leaving one with `win.erase(win.find(a[i-w]))` O(log w) (not
  `erase(value)`, which removes all equal copies), max = `*win.rbegin()` O(1) -> **O(n log w)**.
* `priority_queue` of (value, index) with **lazy deletion**: push each element O(log n); before reading the max, pop while `top.index <= i - w`.
  Each element is pushed once and popped at most once: **O(n log n)** (heap size can reach n).
* Monotonic `deque` of indices (decreasing values): each index is pushed once and popped at most once, so **O(n) total**, amortized O(1) per item.

### Design 8 - Range queries on a changing set

*Maintain a set of integers; operations: `add(x)`, `remove(x)`, `listRange(a,b)`, and `countRange(a,b)`.*

* `set<int> S`. `add`/`remove` O(log n). `listRange`: `it = S.lower_bound(a)` O(log n), then walk until `*it > b`: **O(log n + m)**
  where m = number of reported elements (slide's lower_bound/upper_bound loop). `countRange` with `std::distance(lower_bound(a), upper_bound(b))` is **O(log n + m)** -
  not O(log n).
* If the set is **static** (no updates): store a sorted `vector`: build O(n log n), then `countRange` = `upper_bound(b) - lower_bound(a)` is **O(log n)** because vector iterators are random access (subtraction O(1)).
* So: dynamic + range -> `set`; static + counts -> sorted `vector`. A hash can't answer range queries at all.

### Design 9 - Group anagrams

*n words of length at most L.*

* Key for a word = its letters sorted: sort costs O(L log L) (or O(L + 26) with a letter-count array as the key).
* `unordered_map<string, vector<string>> groups`: `groups[key].push_back(word)`: the hash of an L-character key is O(L) average; push_back amortized O(1).
* Total with sorted keys: n x (O(L log L) + O(L)) = **O(n L log L) average**; with count keys **O(nL) average**.
* With `map` instead: each lookup does O(log n) key comparisons costing O(L) each -> O(n L log n) worst-case guaranteed (plus key building).

### Design 10 - Running median

*Numbers arrive one at a time; after each, report the median.*

* Two heaps: a max-heap `lo` of the smaller half, a min-heap `hi` of the larger half, sizes differing by at most 1.
* `add(x)`: push into one heap O(log n); if sizes differ by more than 1, move one top: pop O(log n) + push O(log n). Median = top of the larger heap (or average of the two tops): **O(1)**.
* n numbers: **O(n log n) total**. Naive alternative: keep a sorted `vector` and insert in place: O(n) shifting per insertion -> O(n^2).
* A `multiset` plus a median iterator moved one step per insertion also gives O(log n) per add.

### Design 11 - Intersection of two arrays (sizes n <= m)

* Hash the smaller (O(n) average), scan the larger and test each element (O(m) average): **O(n+m) average**, O(nm) worst; O(n) space.
* Sort both: O(n log n + m log m), then merge-like two pointers O(n+m): **O(n log n + m log m) worst-case guaranteed**.
* Better guarantee: sort only the smaller (O(n log n)) and binary-search each of the m elements: **O((n+m) log n)**.

### Design 12 - Priority scheduler

*Tasks arrive over time with priorities; the CPU repeatedly runs the highest-priority task.*

* `priority_queue<Task>`: push O(log n), pop O(log n) (do not claim O(1) insert, because inserts and deletes alternate).
* n tasks, all eventually run: **O(n log n)**. If all n tasks are known at the start: `make_heap` O(n) + n pops O(n log n) = O(n log n),
  and that is optimal: the run order is the sorted order, so a comparison-based scheduler is Omega(n log n).
* If priorities *change*, a heap cannot find the task: use `set<pair<priority,id>>` with a hash from id to the current pair: update O(log n).

---

### Recurrences you should recognize (divide and conquer)

| Recurrence | Solution | Where |
|---|---|---|
| T(n) = 2T(n/2) + cn | O(n log n) | mergesort; quicksort best/average |
| T(n) = T(n/2) + cn | O(n) (cn(1 + 1/2 + 1/4 + ...) = 2cn) | quickselect average |
| T(n) = T(n-1) + cn | O(n^2) | quicksort / quickselect worst case (pivot always min or max) |
| T(n) = T(n/2) + c | O(log n) | binary search |
| T(n) = 2T(n/2) + c | O(n) | recursion that does O(1) work per node |

---

## 9. Answer template (copy this skeleton)

```
Operations needed: (1) ... (2) ... (3) ...
Design: <structure for (1)> because <reason>; <structure for (2)> because <reason>.
Analysis:
  step 1: <call> costs <O(...)> (reason) x <count> = <total>
  step 2: ...
  Total: sum of steps = O(...)  [average; worst case O(...) because ...]
Space: O(...)
(Tight because ... / Alternative: ... would cost ...)
```

## 10. Traps that cost points (checklist)

* Giving a loose bound; omitting the reason for a bound; omitting "average" for hash costs.
* Dropping `k` or `m` or `L` from the answer; writing log n when the structure has n+k elements.
* Saying heap insert is O(1) (only on average and only for random values) or buildHeap is O(n log n).
* Saying splay trees are O(log n) worst case per operation (it is amortized; single worst case O(n)).
* Using `unordered_map` when you need order, min/max, or a range; using `set` when the problem only asks membership (log n instead of 1).
* `std::distance` on set/list iterators (O(m)); `erase` at the front of a vector (O(n)); `list` random access (O(i)).
* Counting reading input as free: reading n items is O(n).
* Forgetting that a nested "log n" inner call makes the total n log n (the `set` in a loop), and that a copy inside a loop is O(n) per iteration.
* Proposing a design that does not satisfy *all* requirements (e.g., a hash that loses order, a heap that cannot delete an arbitrary item).
* Using a non-textbook version of an algorithm (the AI warning).

## 11. Quick self-test (answers collapsed)

1. A `vector<int>` of size n is built by n `push_back`s. (a) Total? (b) Why not O(n^2)? <details><summary>Answer</summary>(a) O(n). (b) A reallocation copies all current elements but they happen at sizes 1,2,4,...: total copying < 2n; so amortized O(1) per push.</details>
2. k inserts into an AVL tree of size n: total, and tight? <details><summary>Answer</summary>Each insert is O(log(size)) with size <= n+k: O(k log(n+k)). Tight: the last k/2 inserts have size >= n + k/2, each Omega(log(n+k)) (an insert reaches a leaf at depth >= floor(log2(size))).</details>
3. Design: print the 10 most frequent of n integers. <details><summary>Answer</summary>`unordered_map` count O(n) avg; size-10 min-heap over the u distinct pairs: u x O(log 10) = O(u); total O(n) average (k = 10 is a constant), O(n^2) worst for the hash.</details>
4. What is the cost of `for (auto x : v) if (s.find(x) != s.end()) ++c;` with `set s` of size m, |v| = n? <details><summary>Answer</summary>n x O(log m) = O(n log m). With an `unordered_set`: O(n) average, O(nm) worst.</details>
5. Which is asymptotically better for the median of n numbers: heap-based selection or quickselect? <details><summary>Answer</summary>Quickselect O(n) average vs O(n log n) for either heap method (k = n/2). Quickselect's worst case is O(n^2) though; use median-of-3/random pivot or introselect for a guarantee.</details>
