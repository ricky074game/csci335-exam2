# 02 - STL Containers in Coding Questions (hash maps/sets, heaps, ordered sets, vector, list)

> **Priority: very high (this is the "coding" half of the half-of-the-exam that is complexity + coding).** The topics page says
> complexity analysis (including "design a solution and analyze it") and coding questions are **cumulative** and make up **about half
> the points**, "more thorough than Exam 1". The sources of questions you have already seen: the **Leetcode Hashing Questions slide**
> (Contains Duplicate I/II/III, Two Sum, Intersection of Two Linked Lists, Valid Anagram, Longest Substring Without Repeating
> Characters), **HW5 Part 3** (Contains Duplicate II, Repeated DNA Sequences + its complexity with `unordered_map` vs `map`),
> **HW6 Q3/Q4** (Kth Largest in a Stream; doing it on the underlying vector), **HW7 C** (`myHeapSort` with `make_heap`/`pop_heap`), and the
> **HW4 solution** for Contains Duplicate III (a `set` and `lower_bound`). Every answer has two halves: **correct compilable C++**, and a
> **complexity analysis that names the cost of each container operation** (average vs worst for hashing). Writing the code by hand,
> closed book, means you must know the exact method names, return types and costs from memory.

**Conventions used in these notes (and in the bank, `bank/coding.json`)**

- C++11 or later; `using namespace std;` assumed; `#include`s are not graded but know which header each container needs.
- Complexity answers: n = size of the input, m = number of distinct values, k = the parameter of the problem. Say **average** and **worst** for
  `unordered_*`; `set`/`map`/`priority_queue` bounds are worst-case. Tight bounds only (a loose bound earns no credit).
- The professor's style (see HW5 Part 3c, the HW4 solution to Contains Duplicate III, and the Complexity Analysis Practice Questions): list the
  steps, give each its cost ("call `lower_bound()` for O(log k) as stated in the STL documentation"), then **combine**: consecutive steps
  add, nested/looped steps multiply. Finish with the total and the space.
- Every solution in these notes was compiled and run against randomized brute-force tests before it went in.
- The exam's heap *traces* use the **textbook heap** (1-indexed min-heap, see `03-heaps.md`). The STL heap functions use a 0-indexed layout;
  you are never asked to trace their internal array, only to use them and to give their costs.

---

## 1. Start from a worked example: Contains Duplicate II (HW5 Part 3a)

**Problem.** Given `nums` and `k`, is there a pair of equal values at indices at most `k` apart?

Before any theory, watch the data structure work. `nums = {1, 2, 3, 1, 2, 3}`, `k = 3`. The map stores *value -> index of its most recent occurrence*.

| i | nums[i] | map before | lookup result | distance | action | map after |
|---|---------|-----------|---------------|----------|--------|-----------|
| 0 | 1 | {} | absent | - | store 1->0 | {1:0} |
| 1 | 2 | {1:0} | absent | - | store 2->1 | {1:0, 2:1} |
| 2 | 3 | {1:0, 2:1} | absent | - | store 3->2 | {1:0, 2:1, 3:2} |
| 3 | 1 | {1:0, 2:1, 3:2} | found at 0 | 3 - 0 = 3 <= 3 | **return true** | - |

With `k = 2` the same trace does not stop at i = 3 (distance 3 > 2): it *overwrites* 1->3 with the newer position (a later duplicate can only be
closer to a later index), and continues; at i = 4 value 2 was at 1 (distance 3 > 2) and so on; the answer is `false`.

```cpp
bool containsNearbyDuplicate(vector<int>& nums, int k) {
    unordered_map<int, int> lastPos;                 // value -> index of its most recent occurrence
    for (int i = 0; i < (int)nums.size(); ++i) {
        auto it = lastPos.find(nums[i]);             // find does NOT create an entry (unlike operator[])
        if (it != lastPos.end() && i - it->second <= k)
            return true;
        lastPos[nums[i]] = i;                        // insert or overwrite with the newer position
    }
    return false;
}
```

**Complexity (in the professor's words).** The loop runs n times. In each iteration, `find` is O(1) on average (hash the integer, look in one bucket), the comparison
and subtraction are O(1), and the assignment through `operator[]` is O(1) on average. So n x O(1) = **O(n) average**; the worst case, when every key
collides into one bucket, makes each hash operation O(n) and the whole thing **O(n^2)**. Space: the map holds up to n entries, **O(n)**.

Notice what happened in this one example, because it is the template for the whole topic:

1. **Pick the container for the question you keep asking.** "Have I seen this value, and where?" -> hash map from value to position.
2. **One pass**, doing O(1) average work per element -> O(n).
3. **Look before you write** (`find`, not `[]`), then update.
4. **Cost sentence**: name each call's cost, multiply by the loop count, add consecutive parts.

---

## 2. Cost cheat sheet (memorize this table)

Citations are to the cplusplus.com reference pages the HWs point at (`unordered_map`, `map`, `set`, `priority_queue`, `vector`, `list`, `<algorithm>`).

| Container / call | Cost | Notes |
|---|---|---|
| `unordered_map/set`: `find`, `count`, `insert`, `erase(key)`, `operator[]`, `at` | **O(1) average, O(n) worst** | worst case = all keys in one bucket; `insert` may also trigger an (amortized) rehash |
| iterate over a whole `unordered_*` | **O(n)** | as long as the table keeps a sane load factor (HW5 solution 3c); order is arbitrary |
| `unordered_*` range query / min / max / sorted order | **not supported efficiently** | (STL slide) "can't iterate in order or over a range, can't remain sorted, can't efficiently findMin/Max/InRange" |
| `set/map`: `find`, `count`, `insert`, `erase(key)`, `lower_bound`, `upper_bound` (member functions) | **O(log n)** worst case | balanced BST, typically red-black tree (STL slide) |
| `set/map`: iterate all, `++it` | O(n) total, O(1) amortized per step | in-order traversal |
| `std::lower_bound(s.begin(), s.end(), x)` on a `set` | **O(n)** (!) | only log n comparisons, but bidirectional iterators advance linearly |
| `priority_queue`: `top()` | O(1) | returns `const T&`; undefined on empty |
| `priority_queue`: `push`, `pop` | **O(log n)** | `push` = `push_back` + `push_heap`; `pop` = `pop_heap` + `pop_back`; `pop` returns **void** |
| `priority_queue` range constructor | O(n) | constructs the vector then `make_heap` |
| `make_heap(first,last)` | **O(n)** | cplusplus.com: up to 3n comparisons |
| `push_heap`, `pop_heap` | O(log n) | `push_heap`: new element must already be at `back()`; `pop_heap` moves the root to `back()` |
| `sort_heap` | O(n log n) | needs a valid heap range as input |
| `std::sort` | O(n log n) | introsort |
| `vector`: `operator[]`, `back`, `pop_back` | O(1) | |
| `vector`: `push_back` | **amortized O(1)** | occasional reallocation, O(n) |
| `vector`: `insert`/`erase` in the middle or at the front | **O(n)** | shifts the tail |
| `list`: `insert(pos,x)`, `erase(pos)`, `push_front/back`, `pop_front/back` | **O(1)** | needs an iterator already |
| `list`: `splice` of one element or a whole list | O(1) | |
| `list`: `size()` | O(1) (C++11) | |
| `list`: find the k-th element | O(k) | no random access |
| `list::sort` | O(n log n) | `std::sort` needs random access, so `list` has its own |
| `string::substr(pos, len)` | O(len) | copies; `unordered_map<string,..>` hashing a string is O(length) |

**Why is hashing worst case O(n)?** (HW5 / slides) All n keys can land in one bucket (bad hash function or adversarial input), and a bucket is a list: searching it is linear.
**Why do we still quote O(1)?** With a good hash function and the table rehashed to keep the load factor bounded (by default `max_load_factor() == 1.0`, the same "lambda > 1 -> rehash" rule you used for separate chaining in HW5), the expected bucket length is a constant.

### Check yourself

1. Which is faster in the worst case for n inserts: `unordered_set` or `set`? What about on average?
2. What is the cost of `std::lower_bound(s.begin(), s.end(), 5)` when `s` is a `std::set<int>`? What should you call instead?

<details><summary>Answer</summary>

1. `set` is O(n log n) worst case (each insert O(log n), deterministic); `unordered_set` is O(n^2) worst case (each insert O(n) if all keys collide). On average the hash set wins: O(n) vs O(n log n).
2. O(n): the number of comparisons is O(log n) but each step of the "binary search" has to advance a bidirectional iterator linearly. Use the member `s.lower_bound(5)`, O(log n).
</details>

---

## 3. The hash containers: exact API, and the traps

Header `<unordered_map>` / `<unordered_set>`. Types: `unordered_map<Key, T>`, `unordered_set<Key>`. Elements of a map are `pair<const Key, T>` (use `->first`, `->second`).

| Call | Signature (simplified) | Returns | Average / worst |
|---|---|---|---|
| lookup | `iterator find(const Key& k)` | iterator to the element, or `end()` | O(1) / O(n) |
| count | `size_type count(const Key& k) const` | 0 or 1 | O(1) / O(n) |
| insert | `pair<iterator,bool> insert(const value_type& v)` | `.second == false` if the key was already there (nothing changed) | O(1) / O(n) |
| erase by key | `size_type erase(const Key& k)` | number removed (0 or 1) | O(1) / O(n) |
| erase by iterator | `iterator erase(iterator pos)` | the **next** iterator | O(1) / O(n) |
| bracket (map only) | `T& operator[](const Key& k)` | reference to the value; **creates** the element (value-initialized) if absent | O(1) / O(n) |
| checked access (map only) | `T& at(const Key& k)` | reference; **throws** `out_of_range` if absent | O(1) / O(n) |
| size | `size()`, `empty()`, `clear()` | | O(1) |
| range constructor | `unordered_set<int> s(v.begin(), v.end())` | | O(n) average |
| `reserve(n)` | pre-allocates buckets for n elements | avoids rehashing | O(n) |

### 3.1 `operator[]` creates entries (HW5 hint)

The HW5 text spells out the consequences; here they are as code:

```text
unordered_map<string,int> m;
m["a"]++;                    // OK: absent -> created with value 0 -> incremented to 1  (counting idiom)
m["b"] = 7;                  // OK: insert or overwrite
if (m["zzz"] == 0) { }       // BUG if you only meant to ask "is zzz present?":  m now has zzz -> 0 in it, size grew
auto it = m.find("zzz");     // correct lookup: it == m.end(), the map is unchanged
```

- "insert x if not present": `m[x]` (or `insert`).
- "count occurrences": `++m[x]` (`m[x]++` is equivalent for the effect).
- "is x present?": `m.find(x) != m.end()` or `m.count(x)`; **never `m[x]`**.
- `const` maps cannot use `[]` (it might insert), and `at()` is the lookup that throws instead of inserting.
- `++m[x] == 2` is a neat idiom because `operator[]` returns a reference and the pre-increment returns the **new** value (the HW5 "refactored for better runtime" solution).

### 3.2 Iterating, erasing, and iterator invalidation

```text
for (const auto& kv : m)   // kv.first, kv.second ; 'const auto&' avoids copying the pair (and the string!) each time
    ...
```
- Iteration visits all n elements: O(n) (given a reasonable load factor), but in **no useful order**. If a question needs "the first element in input order", iterate the *input vector*, not the map (see `firstUnique` below).
- `erase(iterator)` invalidates only the erased iterator. The loop `for (it = m.begin(); it != m.end(); ++it) if (...) m.erase(it);` is **undefined behavior**; write `if (...) it = m.erase(it); else ++it;`.
- **Insert can rehash**: if a rehash occurs, *all iterators are invalidated* (references and pointers to elements stay valid). Never hold an iterator across an insertion you do not control; never insert while iterating.
- Storing an *iterator* of a `list` in a map (LRU cache below) is fine because list iterators stay valid; storing iterators of an unordered_map or a vector long-term is not.

### 3.3 Hashing keys

- `int`, `char`, `string`, pointers (`ListNode*`) have built-in `std::hash`. Hashing a `string` is **O(length)** - say so in a complexity analysis (HW5: sequences of fixed length 10 are an "expensive O(1)").
- `pair<int,int>` has **no** `std::hash`: `unordered_map<pair<int,int>,int>` does not compile. Options: write a hash functor (third template argument), encode the pair in a `long long`, or use an ordered `map` (pairs have `operator<`).
- A custom class used as a key needs `operator==` and a hash (the textbook's `hash<Employee>` functor in 5.12).

### Check yourself

1. After `unordered_map<int,int> m; if (m[5] == 0) cout << "no";` what is `m.size()`?
2. What does `s.insert(x).second` tell you for an `unordered_set<int> s`?
3. Why is `unordered_map<pair<int,int>,int> g;` a compile error and how do you fix it?

<details><summary>Answer</summary>

1. 1: `m[5]` inserted the key 5 with value 0. Use `m.count(5)` or `find` to test membership.
2. `true` if x was newly inserted, `false` if it was already present (the set is unchanged). One call both tests and inserts.
3. There is no `std::hash<std::pair<int,int>>`. Provide a hash functor as the third template argument, encode the pair into a single `long long`, or use `map<pair<int,int>,int>` (O(log n) per access instead of O(1) average).
</details>

---

## 4. Hash patterns, one problem each (code, then the full analysis)

All of these are in `bank/coding.json` with a stub and a rubric; here is the pattern list so you recognize them.

| Pattern | What the hash stores | Problems |
|---|---|---|
| **Seen-set** | values seen so far | Contains Duplicate I |
| **Last position** | value -> latest index | Contains Duplicate II, Longest Substring Without Repeating Characters |
| **Counts** | value -> multiplicity | Valid Anagram, Repeated DNA, first non-repeating, group/frequency, pairs with difference |
| **Complement** | value -> index, ask for `target - x` | Two Sum |
| **Prefix sums** | prefix value -> count | subarray sum equals k |
| **Canonical key** | canonical form -> list | group anagrams |
| **Sliding window** | the contents of the last k elements | duplicates within distance, distinct values per window |
| **Identity (address) set** | pointers | Intersection of two linked lists |
| **Run start** | values; test `x-1` | longest consecutive sequence |

### 4.1 Contains Duplicate (I) - seen-set

```cpp
bool containsDuplicate(const vector<int>& nums) {
    unordered_set<int> seen;
    for (int x : nums) {
        if (!seen.insert(x).second)   // insert returns pair<iterator,bool>; .second == false means x was already there
            return true;
    }
    return false;
}
```

- Loop: n iterations. `insert` on an `unordered_set<int>`: O(1) average (hash of an int is O(1), one bucket), O(n) worst. `.second`, `return`: O(1).
- **O(n) average, O(n^2) worst.** Space O(n).
- Compare: sort + adjacent compare is O(n log n) time (O(1) extra space if in place); `set<int>` is O(n log n) worst case.

### 4.2 Two Sum - complement lookup

```cpp
vector<int> twoSum(const vector<int>& nums, int target) {
    unordered_map<int, int> indexOf;                 // value -> index of an EARLIER element with that value
    for (int i = 0; i < (int)nums.size(); ++i) {
        auto it = indexOf.find(target - nums[i]);    // is the complement already seen?
        if (it != indexOf.end())
            return {it->second, i};
        indexOf[nums[i]] = i;                        // store after the lookup so an element is never paired with itself
    }
    return {};                                       // no pair (problem statement guarantees one exists)
}
```

Look up `target - nums[i]` **before** inserting `nums[i]`: then an element is never paired with itself, and `{3, 3}` with `target = 6` still works (the first 3 is in the map when the second arrives).
Loop n times x (`find` O(1) avg + `operator[]` O(1) avg) = **O(n) average**, O(n^2) worst; space O(n). Brute force is O(n^2); sorting + two pointers O(n log n) (but loses the indices).

### 4.3 Valid Anagram - counting

```cpp
bool isAnagram(const string& s, const string& t) {
    if (s.size() != t.size()) return false;          // different lengths can never be anagrams
    unordered_map<char, int> count;
    for (char c : s) ++count[c];                     // count[c]++ creates 0 then increments
    for (char c : t) {
        auto it = count.find(c);
        if (it == count.end() || it->second == 0)    // t has a letter s doesn't have (or has too many of it)
            return false;
        --it->second;
    }
    return true;                                     // equal lengths + no count went negative => all counts are 0
}
```

Equal lengths + no count ever goes below zero => all counts end at zero. Two loops of n x O(1) average = **O(n) average**; space O(sigma) (alphabet), i.e. O(1) for 26 letters.
Sorting both strings and comparing is O(n log n).

### 4.4 Repeated DNA Sequences (HW5 3b) and its complexity (3c)

```cpp
vector<string> findRepeatedDnaSequences(const string& s) {
    unordered_map<string, int> count;                // 10-letter sequence -> times seen so far
    vector<string> answer;
    for (size_t i = 0; i + 10 <= s.size(); ++i) {
        string seq = s.substr(i, 10);                // O(10) = O(1)
        if (++count[seq] == 2)                       // operator[] creates 0 on first sight; becomes 2 exactly once
            answer.push_back(seq);                   // report each repeated sequence only once
    }
    return answer;
}
```

`++count[seq] == 2` pushes a sequence exactly once, at its second sighting. (The official first solution counts every substring and then loops over the map pushing counts > 1, also correct.)

**Unordered map (professor's 3c answer, condensed).** O(n) substrings; `substr(i,10)` is an "expensive" O(1) (10 characters); hashing a 10-character string is another "expensive" O(1); the bucket access and the increment are O(1) average. So O(1) per substring x O(n) substrings = **O(n) average**; iterating the hash at the end is O(n) given a minimum load factor, so O(n) overall.

**Ordered `map`.** Replace `unordered_map` by `map` and nothing else changes; but every access is a tree search of O(log n) comparisons (each comparison of two 10-character strings is O(1)), so **O(n log n)** worst case.

### 4.5 Longest Substring Without Repeating Characters - last position + window

```cpp
int lengthOfLongestSubstring(const string& s) {
    unordered_map<char, int> last;                   // char -> index of its most recent occurrence
    int best = 0;
    int start = 0;                                   // current window is s[start..i]
    for (int i = 0; i < (int)s.size(); ++i) {
        auto it = last.find(s[i]);
        if (it != last.end() && it->second >= start) // repeat INSIDE the window (occurrences before start don't count)
            start = it->second + 1;                  // jump the left edge just past the previous occurrence
        last[s[i]] = i;
        best = max(best, i - start + 1);
    }
    return best;
}
```

- `start` is the left edge of the window `s[start..i]`; it only moves right. The test `it->second >= start` is the whole trick: a character last seen **before** `start` is not in the window any more.
- Trace `"abba"`: i=0 `a` window `a`, best 1 | i=1 `b` window `ab`, best 2 | i=2 `b` last seen at 1 >= start 0 so start = 2, window `b`, best 2 | i=3 `a` last seen at 0 < start 2, **no jump**, window `ba`, best 2. Without the `>= start` test, start would move back to 1 and report 3 (wrong).
- **O(n) average**: one pass, n iterations x (`find` O(1) + `operator[]` O(1) + `max` O(1)); no inner loop. Space O(min(n, sigma)).
- Brute force (for each start extend until a repeat) is O(n x min(n, sigma)): O(n^2) for big alphabets. The map lets the left edge **jump** past the previous occurrence instead of re-scanning.

### 4.6 Intersection of Two Linked Lists - hash the *nodes*

```cpp
ListNode *getIntersectionNode(ListNode *headA, ListNode *headB) {
    unordered_set<ListNode*> seen;                   // store node ADDRESSES, not values
    for (ListNode *p = headA; p != nullptr; p = p->next)
        seen.insert(p);
    for (ListNode *p = headB; p != nullptr; p = p->next)
        if (seen.count(p))                           // first node of B that is also in A
            return p;
    return nullptr;
}
```

Store **addresses** (`ListNode*`), never values: two different nodes can hold equal values; "intersection" means the *same node*. Lists of lengths m and n: m inserts + at most n lookups, each O(1) average => **O(m + n) average**, space O(m).
The O(1)-space two-pointer version is worth knowing:

```cpp
ListNode *getIntersectionNodeTwoPointers(ListNode *headA, ListNode *headB) {
    ListNode *a = headA, *b = headB;
    while (a != b) {                                 // each pointer walks lenA + lenB nodes in total
        a = (a != nullptr) ? a->next : headB;
        b = (b != nullptr) ? b->next : headA;
    }
    return a;                                        // the intersection node, or nullptr if there is none
}
```

Each pointer walks lenA + lenB nodes, so they meet at the first shared node (or both reach `nullptr` together): **O(m + n) worst case, O(1) space**.

### 4.7 Counting, first non-repeating element

```cpp
int firstUnique(const vector<int>& nums) {
    unordered_map<int, int> count;
    for (int x : nums) ++count[x];                   // pass 1: count every value
    for (int i = 0; i < (int)nums.size(); ++i)       // pass 2: scan IN ORIGINAL ORDER (hash order is arbitrary)
        if (count.at(nums[i]) == 1)                  // at() = lookup that never creates an entry
            return i;
    return -1;
}
```

Two passes: count with a hash, then scan the **original order** and return the first count of 1 (iterating the map would give an arbitrary order). O(n) + O(n) = **O(n) average**; space O(n).

### 4.8 Group by canonical key

```cpp
vector<vector<string>> groupAnagrams(const vector<string>& words) {
    unordered_map<string, vector<string>> groups;    // sorted letters -> all words with those letters
    for (const string& w : words) {
        string key = w;
        sort(key.begin(), key.end());                // O(L log L)
        groups[key].push_back(w);                    // hash key O(L); [] creates an empty vector the first time
    }
    vector<vector<string>> result;
    result.reserve(groups.size());
    for (auto& kv : groups)
        result.push_back(move(kv.second));           // O(1) per group (moves the vector)
    return result;
}
```

n words of length <= L: sorting each key O(L log L), hashing/comparing keys O(L), so **O(n L log L)** average; space O(nL). `groups[key]` creating an empty vector is the *useful* behavior of `operator[]` here.

### 4.9 Prefix sums + hash: subarray sum equals k

```cpp
int subarraySum(const vector<int>& nums, int k) {
    unordered_map<long long, int> seen;              // prefix sum value -> number of prefixes with that sum
    seen[0] = 1;                                     // the empty prefix
    long long sum = 0;
    int count = 0;
    for (int x : nums) {
        sum += x;                                    // sum = nums[0] + ... + nums[i]
        auto it = seen.find(sum - k);                // a subarray ending at i sums to k iff some earlier prefix = sum - k
        if (it != seen.end()) count += it->second;
        ++seen[sum];
    }
    return count;
}
```

`seen[v]` = number of earlier prefixes with sum `v`. A subarray ending here has sum k iff an earlier prefix equals `sum - k`. Initial `seen[0] = 1` is the empty prefix. n iterations x O(1) average = **O(n) average**, space O(n). Works with negative numbers (a sliding window would not).

### 4.10 Sliding window with a set / a count map

```cpp
bool hasDuplicateWithin(const vector<int>& a, int d) {
    unordered_set<int> window;                       // before iteration i: the values at indices i-d .. i-1
    for (int i = 0; i < (int)a.size(); ++i) {
        if (window.count(a[i])) return true;
        window.insert(a[i]);
        if (i >= d)
            window.erase(a[i - d]);                  // a[i-d] is now too far from index i+1
    }
    return false;
}
```

Window invariant before iteration i: the set holds `a[i-d .. i-1]`. **O(n) average**, space **O(min(n, d))** (smaller than the map solution's O(n) when d is small).

```cpp
vector<int> distinctInWindows(const vector<int>& a, int k) {   // assumes k >= 1
    vector<int> result;
    unordered_map<int, int> count;                   // value -> occurrences inside the current window
    for (int i = 0; i < (int)a.size(); ++i) {
        ++count[a[i]];                               // a[i] enters the window
        if (i >= k) {                                // a[i-k] leaves the window
            auto it = count.find(a[i - k]);
            if (--it->second == 0)
                count.erase(it);                     // erase by iterator: O(1), no second lookup
        }
        if (i >= k - 1)
            result.push_back((int)count.size());     // number of distinct values = number of keys
    }
    return result;
}
```

When a count reaches 0 you **must erase** the key, otherwise `size()` over-counts distinct values. **O(n) average**, space O(k).

### 4.11 Longest consecutive run - why nested loops can still be O(n)

```cpp
int longestConsecutive(const vector<int>& nums) {
    unordered_set<int> s(nums.begin(), nums.end());          // O(n) average; also removes duplicates
    int best = 0;
    for (int x : s) {
        if (s.count(x - 1)) continue;                        // x - 1 exists, so x is NOT the start of a run
        int y = x;
        while (s.count(y + 1)) ++y;                          // walk the run starting at x
        best = max(best, y - x + 1);
    }
    return best;
}
```

The inner `while` only runs from a *run start* (`x - 1` absent). Each run is walked once, runs are disjoint, so the inner loop's **total** work over the whole call is at most the number of distinct values: O(n), not O(n) per element. Everything else is n x O(1) average. **O(n) average**. (Sorting would be O(n log n).)

### 4.12 Pairs with a given difference, intersection, missing numbers

```cpp
long long countPairsWithDiff(const vector<int>& a, int k) {
    unordered_map<long long, int> count;             // value -> how many EARLIER elements have it
    long long pairs = 0;
    for (int x : a) {
        auto it = count.find((long long)x - k);      // earlier element equal to x - k
        if (it != count.end()) pairs += it->second;
        if (k != 0) {                                // for k == 0, x - k and x + k are the same value: count it once
            it = count.find((long long)x + k);       // earlier element equal to x + k
            if (it != count.end()) pairs += it->second;
        }
        ++count[x];                                  // insert x only AFTER looking, so i < j is respected
    }
    return pairs;
}
```

Inserting `x` *after* the lookups enforces `i < j`; `k == 0` must not be double counted. **O(n) average**.

```cpp
vector<int> intersectDistinct(const vector<int>& a, const vector<int>& b) {
    unordered_set<int> inA(a.begin(), a.end());      // O(|a|) average
    vector<int> result;
    for (int x : b)
        if (inA.erase(x) > 0)                        // erase(key) returns how many were removed (0 or 1) => each value reported once
            result.push_back(x);
    return result;
}
```

`erase(key)` returns how many were removed, so a hit is reported only once. O(m + n) average.

```cpp
vector<int> findMissingNoHash(const vector<int>& nums) {
    int n = (int)nums.size();
    vector<bool> present(n + 1, false);              // direct addressing: value v lives at index v
    for (int x : nums) present[x] = true;
    vector<int> missing;
    for (int v = 1; v <= n; ++v)
        if (!present[v]) missing.push_back(v);
    return missing;
}
```

When the keys are small dense integers (here 1..n), **direct addressing** (a `vector<bool>`) is a hash table with the identity hash and no collisions: O(n) *worst case*. Reach for a hash container when the key universe is large or sparse.

### 4.13 Check yourself

1. In Contains Duplicate II, why is it enough to remember only the **latest** index of each value?
2. What would go wrong in Longest Substring Without Repeating Characters if you wrote `start = last[s[i]] + 1;` without the `>= start` test?
3. Give the complexity of Two Sum if you used `map<int,int>` instead of `unordered_map<int,int>`.

<details><summary>Answer</summary>

1. If the nearest earlier equal value is more than k away, every older one is even farther, so only the latest can ever make the distance <= k; overwriting loses nothing.
2. The left edge could move **backwards** when a character was last seen outside the current window (`"abba"`: at the last `a`, start would go from 2 back to 1, giving the wrong answer 3 instead of 2).
3. O(n log n): n iterations, each `find` and `operator[]` costs O(log n) in a balanced BST (deterministic worst case, not average).
</details>

---

## 5. Ordered containers: `set`, `map`, `lower_bound`, `upper_bound`

`set<T>` / `map<K,V>` are balanced BSTs (STL slide: typically red-black trees). All the elementary operations are **O(log n)** worst case, and they keep their elements **sorted**, so they support what hashes cannot: smallest/largest (`begin()`, `prev(end())`), neighbors, and **range queries**.

| Call | Meaning | Cost |
|---|---|---|
| `s.lower_bound(x)` | iterator to the first element **>= x** (`end()` if none) | O(log n) |
| `s.upper_bound(x)` | iterator to the first element **> x** | O(log n) |
| `s.find(x)`, `s.insert(x)`, `s.erase(x)` | | O(log n) |
| `s.begin()`, `s.end()`, `++it`, `--it` | | O(1) (amortized for `++`) |
| `std::prev(it)`, `std::next(it)` | neighbor iterator | O(1) |
| `std::distance(it1, it2)` on a set | number of elements between | **O(distance)**, not O(1) |

### 5.1 The range-based search idiom (Leetcode Hashing Questions slide)

```text
elements with lo <= x <= hi   ==   [ s.lower_bound(lo) , s.upper_bound(hi) )
```

Example: `s = {10, 20, 30, 40, 50, 60, 70}`, `lo = 25`, `hi = 55`. `lower_bound(25)` -> 30 (first >= 25). `upper_bound(55)` -> 60 (first > 55). The loop from 30 up to (not including) 60 visits 30, 40, 50. If `hi = 50`: `upper_bound(50)` -> 60 as well, so 50 *is* included - the whole reason for using `upper_bound` on the right end.

```cpp
vector<int> inRange(const set<int>& s, int lo, int hi) {
    vector<int> out;
    if (lo > hi) return out;                         // without this guard the loop below can run past end()
    auto first = s.lower_bound(lo);                  // first element >= lo   : O(log n)
    auto last = s.upper_bound(hi);                   // first element >  hi   : O(log n)
    for (auto it = first; it != last; ++it)          // m steps, each O(1) amortized
        out.push_back(*it);
    return out;
}
```

**O(log n + m)** for m reported elements: two tree searches, then m steps of `++it`. Guard `lo > hi` (the iterator range would be backwards and the loop would run off `end()`). The count of elements in the range cannot be had in O(log n) with the STL (the iterator difference costs O(m)).

**Trap: `std::lower_bound(s.begin(), s.end(), x)` compiles and returns the right answer but costs O(n).** Use the member function.

### 5.2 Contains Duplicate III (HW4 solution) - sliding window of an ordered set

We need an earlier value in `[x - valueDiff, x + valueDiff]` among the last `indexDiff` positions. Keep exactly those values in a `set`; the smallest value `>= x - valueDiff` is the best candidate (if it is not <= `x + valueDiff`, nothing in the window is).

```cpp
bool containsNearbyAlmostDuplicate(vector<int>& nums, int indexDiff, int valueDiff) {
    set<long long> window;                           // the values at the last indexDiff positions
    for (int i = 0; i < (int)nums.size(); ++i) {
        long long x = nums[i];                       // long long so x - valueDiff / x + valueDiff cannot overflow
        auto lb = window.lower_bound(x - valueDiff); // smallest value in the window that is >= x - valueDiff
        if (lb != window.end() && *lb <= x + valueDiff)
            return true;                             // that value lies in [x - valueDiff, x + valueDiff]
        window.insert(x);
        if (i >= indexDiff)                          // keep a fixed-size sliding window
            window.erase((long long)nums[i - indexDiff]);
    }
    return false;
}
```

**Complexity (HW4 solution 2).** The loop runs n times; the set never holds more than k = `indexDiff` elements, so `lower_bound` is O(log k), `insert` O(log k), `erase` O(log k); `end()` and the Boolean logic are O(1). A sequence of O(log k) and O(1) operations is O(log k); n times gives **O(n log k)**, worst case. Space O(k). A hash set cannot be used because it cannot find the **successor** `lower_bound`; scanning the window would cost O(k) per element, O(nk) total.

### 5.3 Closest value / predecessor / successor

```cpp
int closest(const set<int>& s, int x) {            // s must be non-empty; ties go to the smaller value
    auto it = s.lower_bound(x);                      // first element >= x
    if (it == s.end()) return *prev(it);             // every element is < x: the largest one is closest
    if (it == s.begin()) return *it;                 // every element is >= x: the smallest one is closest
    auto before = prev(it);                          // largest element < x
    return (x - *before <= *it - x) ? *before : *it;
}
```

`lower_bound` gives the successor-or-equal; `prev` of it the predecessor; compare the two distances. O(log n). Handle `it == end()` and `it == begin()` before dereferencing or stepping back.

### 5.4 `map` specifics

- `map<K,V>::lower_bound(k)` returns an iterator to a `pair<const K,V>`: use `it->first`, `it->second`.
- `m[k]` has the same create-if-absent behavior as `unordered_map::operator[]`; `m.at(k)` throws; `m.find(k)` is the lookup that does not insert. A `const map` cannot use `[]`.
- Iterating a map visits keys in **sorted order** (an advantage over the hash map: O(n) for a sorted dump; the hash map gives no order).

### Check yourself

1. `s = {5, 10, 15, 20}`. What do `s.lower_bound(10)`, `s.upper_bound(10)`, `s.lower_bound(11)`, `s.lower_bound(25)` return?
2. Why is `Contains Duplicate III` O(n log k) and not O(n log n)?
3. Why can't you answer a range query efficiently with an `unordered_set`?

<details><summary>Answer</summary>

1. Iterators to 10, 15, 15, and `s.end()`.
2. Because the set is a sliding window holding at most k elements, so each tree operation is O(log k), not O(log n).
3. A hash set has no order: no `lower_bound`, no in-order traversal. You would have to examine all n elements: O(n) per query.
</details>

---

## 6. Heaps in the STL: `priority_queue` and the `<algorithm>` heap functions

### 6.1 `priority_queue` (header `<queue>`)

- **Max-heap by default**: `priority_queue<int> pq;` puts the **largest** on top.
- **Min-heap**: `priority_queue<int, vector<int>, greater<int> > pq;` (three template arguments: element type, underlying container, comparator). HW6 gives this syntax; memorize it. (In C++11 the old `> >` spacing is not required, but is harmless.)
- Underlying container: `vector` by default (STL slide: "priority queues use vectors by default and behave as heaps"; they need random access, so no `list`).

| Call | Returns | Cost |
|---|---|---|
| `void push(const T&)` | nothing | O(log n) |
| `const T& top() const` | the highest-priority element (**undefined if empty**) | O(1) |
| `void pop()` | **nothing** (void!) | O(log n) |
| `bool empty() const`, `size_t size() const` | | O(1) |
| `priority_queue(first, last)` | build from a range | O(n) (make_heap) |
| (no `decreaseKey`, no iteration, no `find`, no access to the k-th element) | | |

**The "remove and use the smallest" idiom:** `int x = pq.top(); pq.pop();`  (`int x = pq.pop();` does not compile.)

**Trace of the min-heap logic for "kth largest in a stream" (k = 3), using the textbook heap array** (generated with `python tools/study.py heap ...`; the STL stores the same *values* in a 0-indexed layout, which you do not trace). Initial stream `{4, 5, 8, 2}`:

- Add 4, 5, 8 (size < k, just push): the min-heap is `4,5,8`. Then 2 arrives: 2 is not larger than the root 4, so it is discarded. The 3rd largest is `top() = 4`.
- `add(10)`: 10 > 4, so deleteMin then insert. `python tools/study.py heap delete "4,5,8" --count 1` shows the last element 8 going to index 0, the smaller child 5 sliding up to the root, and 8 settling in index 2: final `5,8`; then `python tools/study.py heap insert "5,8" 10` places 10 at index 3 (its parent 5 is not larger): final `5,8,10`. New 3rd largest: `top() = 5` (the three largest are 5, 8, 10).

The reasoning, not the array, is what an exam answer needs: *the k largest values live in a min-heap; the root is the smallest of them = the kth largest.*

### 6.2 Custom comparators

`priority_queue<T, Container, Compare>`: the element on top is the one that is **greatest according to `Compare`** (`Compare(a,b)` true means "a is below b"). With the default `less<T>` the largest is on top. So:

- `greater<T>` => the **smallest** is on top (min-heap).
- For pairs, the default compares `first` then `second`: `priority_queue<pair<int,int>>` is a max-heap on count, then value; `greater<pair<int,int>>` a min-heap.
- A comparator for a lambda: `auto cmp = [](ListNode* a, ListNode* b){ return a->val > b->val; }; priority_queue<ListNode*, vector<ListNode*>, decltype(cmp)> pq(cmp);` (the lambda object must be passed to the constructor).
- When you want "the worst candidate on top so I can evict it" (top-k), define `Compare(a, b)` = "a is *better* than b" so the best is "smallest" and the worst is on top (see top-k words in the bank).

### 6.3 The heap algorithms on a vector (header `<algorithm>`)

| Call | What it does | Cost (cplusplus.com) |
|---|---|---|
| `make_heap(first, last [, comp])` | rearranges the range into a heap (max-heap by default) | O(n) (up to 3n comparisons) |
| `push_heap(first, last [, comp])` | the new element must already be at `*(last-1)`; percolates it up | O(log n) |
| `pop_heap(first, last [, comp])` | swaps the root with `*(last-1)`, restores the heap on `[first, last-1)`; the old root is now at `*(last-1)`, **still in the container** | O(log n) (up to 2 log n comparisons) |
| `sort_heap(first, last [, comp])` | turns a heap into a sorted range (ascending w.r.t. `comp`) | O(n log n) |
| `is_heap` | | O(n) |

- Use the **same comparator in every call** (`greater<int>()` for a min-heap), or the heap is corrupted.
- Insert: `v.push_back(x); push_heap(v.begin(), v.end());`. Remove the root: `pop_heap(v.begin(), v.end()); v.pop_back();`.

> *A worked HW7 answer goes here. It is added to the public version after HW7 is due (Nov 17).*

> *A worked HW6 answer goes here. It is added to the public version after HW6 is due (Nov 10).*

### 6.5 More heap patterns

**Top-k by frequency (min-heap of size k over the map entries).**

```cpp
vector<int> topKFrequent(const vector<int>& nums, int k) {
    unordered_map<int, int> count;
    for (int x : nums) ++count[x];                           // O(n) average
    typedef pair<int, int> P;                                // (count, value)
    priority_queue<P, vector<P>, greater<P>> heap;           // MIN-heap on count: top = least frequent of the k kept
    for (const auto& kv : count) {                           // m = number of distinct values
        heap.push(P(kv.second, kv.first));                   // O(log k)
        if ((int)heap.size() > k) heap.pop();                // O(log k): evict the least frequent
    }
    vector<int> result;
    while (!heap.empty()) {
        result.push_back(heap.top().second);
        heap.pop();
    }
    reverse(result.begin(), result.end());                   // most frequent first
    return result;
}
```

Counting n x O(1) = O(n); m map entries x (`push` O(log k) + `pop` O(log k)) = O(m log k); output O(k log k). **O(n + m log k) <= O(n log k)**. It is a **min**-heap because the thing we repeatedly discard is the *least* frequent of the k kept.

**Merge k sorted linked lists with a heap.**

```cpp
ListNode *mergeKLists(vector<ListNode*>& lists) {
    auto cmp = [](ListNode *a, ListNode *b) { return a->val > b->val; };   // greater-than => MIN-heap on val
    priority_queue<ListNode*, vector<ListNode*>, decltype(cmp)> heap(cmp);
    for (ListNode *head : lists)
        if (head != nullptr) heap.push(head);                // one candidate per list
    ListNode dummy(0);
    ListNode *tail = &dummy;
    while (!heap.empty()) {
        ListNode *node = heap.top();                         // smallest front node among all lists
        heap.pop();
        tail->next = node;
        tail = node;
        if (node->next != nullptr) heap.push(node->next);    // its list's next node becomes a candidate
    }
    return dummy.next;
}
```

Heap size <= k; every one of the N nodes is pushed once and popped once: N x O(log k) = **O(N log k)**, space O(k). Merging lists one after another is O(Nk); concatenating + sorting is O(N log N).

**Running median with two heaps.**

```cpp
class MedianFinder {
    priority_queue<int> lo;                                  // MAX-heap: the smaller half (top = its largest)
    priority_queue<int, vector<int>, greater<int>> hi;       // MIN-heap: the larger half (top = its smallest)
public:
    void addNum(int num) {
        if (lo.empty() || num <= lo.top()) lo.push(num);
        else hi.push(num);
        if (lo.size() > hi.size() + 1) {                     // rebalance: sizes must satisfy |lo| - |hi| in {0, 1}
            hi.push(lo.top());
            lo.pop();
        } else if (hi.size() > lo.size()) {
            lo.push(hi.top());
            hi.pop();
        }
    }
    double findMedian() const {                              // precondition: at least one number added
        if (lo.size() > hi.size()) return lo.top();
        return (lo.top() + (double)hi.top()) / 2.0;
    }
};
```

`lo` (max-heap) holds the smaller half, `hi` (min-heap) the larger half, sizes differ by at most one. `addNum` = O(1) `top`s + O(1) number of O(log n) pushes/pops = **O(log n)**; `findMedian` **O(1)**. A sorted `vector` costs O(n) per insert (shifting).

**Sort a k-sorted array with a heap of size k + 1.**

```cpp
void sortKSorted(vector<int>& a, int k) {
    priority_queue<int, vector<int>, greater<int>> heap;     // MIN-heap holding at most k+1 elements
    size_t out = 0;                                          // next position of a to overwrite
    for (size_t i = 0; i < a.size(); ++i) {
        heap.push(a[i]);                                     // a[i] has been read, so a[out] (out <= i) is free
        if (heap.size() > (size_t)k) {
            a[out++] = heap.top();                           // smallest of the window is the next sorted element
            heap.pop();
        }
    }
    while (!heap.empty()) {                                  // flush the last <= k elements
        a[out++] = heap.top();
        heap.pop();
    }
}
```

n pushes and n pops on a heap of size <= k+1: **O(n log k)**, space O(k). `std::sort` would be O(n log n).

**The selection problem both ways (textbook 6.4 / 6A, 6B).**

```cpp
vector<int> kSmallestBuildHeap(const vector<int>& a, int k) {      // textbook 6A: buildHeap + k deleteMins
    priority_queue<int, vector<int>, greater<int>> heap(a.begin(), a.end());   // range constructor = make_heap: O(n)
    vector<int> out;
    for (int i = 0; i < k && !heap.empty(); ++i) {
        out.push_back(heap.top());
        heap.pop();                                          // O(log n) each
    }
    return out;
}
```

(6A) range constructor = `make_heap` O(n), then k x pop O(log n): **O(n + k log n)**, space O(n).

```cpp
vector<int> kSmallestHeapK(const vector<int>& a, int k) {          // textbook 6B: heap of size k
    priority_queue<int> heap;                                // MAX-heap holding the k smallest seen so far
    for (int x : a) {
        if ((int)heap.size() < k)
            heap.push(x);                                    // O(log k)
        else if (!heap.empty() && x < heap.top()) {          // x beats the largest of the k kept
            heap.pop();                                      // O(log k)
            heap.push(x);                                    // O(log k)
        }
    }
    vector<int> out;
    while (!heap.empty()) {
        out.push_back(heap.top());
        heap.pop();
    }
    reverse(out.begin(), out.end());                         // ascending
    return out;
}
```

(6B) a MAX-heap of size k (top = the largest of the k smallest, the one to evict): **O(n log k)**, space O(k), works on a stream.

For k = O(n / log n), 6A is O(n); for k = sqrt(n), 6A is O(n) and 6B is O(n log n). For huge streams or limited memory use 6B.

### Check yourself

1. Declare a min-heap of `long long`. Declare a max-heap of `pair<int,string>`.
2. What does `pop_heap(v.begin(), v.end())` do to the vector's size?
3. A stream problem asks for the 5 *smallest* values seen so far. Heap type and size?
4. `make_heap` is O(n), yet building a heap by n calls to `push` is O(n log n) worst case. Why the difference?

<details><summary>Answer</summary>

1. `priority_queue<long long, vector<long long>, greater<long long> > h;` and `priority_queue<pair<int,string> > h;` (default = max-heap on first, then second).
2. Nothing: the size is unchanged. The root is swapped to `v.back()` and the heap is repaired on `[begin, end-1)`. You must call `v.pop_back()` yourself.
3. A **max**-heap of size 5: the root is the largest of the five smallest, the element to evict when a smaller value arrives.
4. `make_heap` (buildHeap) percolates *down* from n/2 to 1, and the work is the sum of node heights, which is O(n) (most nodes are near the bottom). `push` percolates *up* by the depth, O(log n) each in the worst case (e.g. strictly decreasing input into a min-heap: every new element percolates all the way to the root), so n of them are O(n log n).
</details>

---

## 7. `vector` and `list` in coding answers

- `vector`: `push_back` amortized O(1); `v[i]` O(1); `insert`/`erase` in the middle or front O(n); `reserve(n)` avoids reallocations. A reallocation invalidates **all** iterators, references and pointers; `insert`/`erase` invalidate iterators at or after the position.
- `list` (doubly linked): `insert(pos,x)`, `erase(pos)`, `push_front/back`, `pop_front/back`, `splice` of one element: **O(1)**; no `operator[]`, reaching the k-th element is O(k). Insert/erase only invalidate iterators to the erased element: **iterators and references to other elements stay valid**, and `splice` keeps the moved element's iterator valid. `list::sort()` is O(n log n) (and `std::sort` does not work on a list).
- Use `vector` when you need positions/random access or just a sequence you append to (HW "seminar" practice question: `push_back` in order of arrival, then read every 100th). Use `list` when you need O(1) insertion or removal *given an iterator*, e.g. an LRU order.

**LRU cache: `list` + `unordered_map` of iterators.**

```cpp
class LRUCache {
    int cap;
    list<pair<int, int>> items;                                  // (key, value); front = most recently used
    unordered_map<int, list<pair<int, int>>::iterator> where;    // key -> its node in items
public:
    LRUCache(int capacity) : cap(capacity) {}                    // assumes capacity >= 1
    int get(int key) {
        auto it = where.find(key);
        if (it == where.end()) return -1;
        items.splice(items.begin(), items, it->second);          // move that node to the front: O(1), iterators stay valid
        return it->second->second;
    }
    void put(int key, int value) {
        auto it = where.find(key);
        if (it != where.end()) {                                 // key exists: update and refresh
            it->second->second = value;
            items.splice(items.begin(), items, it->second);
            return;
        }
        if ((int)items.size() == cap) {                          // full: evict the least recently used (back)
            where.erase(items.back().first);
            items.pop_back();
        }
        items.push_front(make_pair(key, value));
        where[key] = items.begin();
    }
};
```

- The list orders keys by recency (front = most recent); the map finds a key's node in O(1) average. Neither alone suffices: a list alone makes `get` O(n); a hash map alone has no recency order.
- `get`: `find` O(1) avg, `splice` O(1). `put`: `find` O(1) avg, then either update + `splice` O(1), or (maybe evict `pop_back` O(1) + `erase(key)` O(1) avg) + `push_front` O(1) + `operator[]` O(1) avg. Everything **O(1) average**; space O(capacity).

### Check yourself

1. Which STL sequence container would you use to maintain an "order of arrival" log of n names, then print every 100th? Why?
2. Why does the LRU cache store a list iterator in the map instead of a position index?

<details><summary>Answer</summary>

1. `vector` with `push_back` (amortized O(1) each, O(n) total), then n/100 random accesses `v[i]`, each O(1): O(n) total. A `list` has no random access.
2. A list iterator stays valid when other nodes are inserted, erased or spliced, and gives O(1) access to the node (to splice or erase it). A position index would change whenever nodes before it move, and indexing into a list is O(n).
</details>

---

## 8. Traps that cost points (checklist before you write a line)

1. **`operator[]` on a lookup** inserts a default element (size grows, the test is wrong). Use `find`/`count`. Counting with `++m[x]` is the *intended* use.
2. **`priority_queue::pop()` returns `void`.** Read `top()` first.
3. **`priority_queue` is a max-heap by default.** A min-heap is `priority_queue<int, vector<int>, greater<int> >`. A wrong heap direction is the classic top-k bug: for the k *largest* use a **min**-heap of size k; for the k *smallest* use a **max**-heap of size k.
4. **`top()` on an empty heap is undefined**; check `empty()` or the problem's guarantees.
5. **Iterator invalidation on unordered containers**: rehash (triggered by `insert`) invalidates all iterators; `erase(it)` invalidates `it` (use `it = m.erase(it)`). References to elements survive a rehash.
6. **Hash iteration order is arbitrary**: for "first / in input order" iterate the input.
7. **`std::lower_bound` on a `set`/`map` is O(n)**; call the member `s.lower_bound(x)`.
8. **`lo > hi` range loops** (`lower_bound(lo)` after `upper_bound(hi)`) run off the end.
9. **No `std::hash<pair>`**; strings hash in O(length), substring copies are O(length).
10. **Keys of the wrong kind**: linked-list intersection needs pointers, not values.
11. **Window bugs**: erase the element that *leaves* the window (`a[i-k]`); erase a key when its count reaches 0 if you use `size()` as "number of distinct".
12. **Overflow**: sums and differences near `INT_MAX` - use `long long` (Contains Duplicate III, prefix sums).
13. **Average vs worst**: write both for hashing; the tree and heap bounds are worst case.
14. **Wrong size in the log**: with a sliding window or a size-k heap the container size is k, so the cost is `log k`, not `log n`.
15. **`pop_heap` does not shrink the vector**, `push_heap` needs the element already at the back; always pass the same comparator.

---

## 9. How to write the complexity paragraph (template)

1. **Name the parameters.** "Let n be the length of `nums`, m the number of distinct values, k the window size."
2. **List each step with its cost**, citing the documentation: "`find` is O(1) average, O(n) worst case; `lower_bound` is O(log k) as stated in the STL documentation; `substr(i,10)` copies 10 characters, O(1)".
3. **Multiply loops, add consecutive steps.** "n iterations x O(1) = O(n); the second pass adds another O(n)".
4. **Justify the size that appears inside the log** (set of at most k elements => log k).
5. **Total, average vs worst, and space.**
6. **One sentence of comparison** with the naive solution if you have time (brute force O(n^2), sorting O(n log n)).

**Model (the HW4 solution in this format):** "O(n log k). We iterate through the input (n values) and for each value we maintain a set of size k and call `lower_bound()` for O(log k); perform some Boolean logic and call `end()`, each O(1); call `insert()` for O(log k); call `erase()` for O(log k). A bunch of O(1) and O(log k) operations in sequence is O(log k), n times = O(n log k)."

---

## 10. What the exam asks (and mini-drills)

Likely forms (from the course materials): (1) "Write a function that ... using an STL container; give its complexity"; (2) a **design** question in the style of the seminar practice question ("what data structure(s) will you use and why? describe and fully analyze the complexity") where the answer chains a hash, a vector, and maybe a heap; (3) the **same code with a different container** ("what if you used an ordered map?", HW5 3c); (4) fix-the-bug and fill-in-the-stub code questions; (5) the cost of a single STL call.

Mini-drills (answers collapsed):

**D1.** Write `bool hasTriple(vector<int>& a)` returning true if some value appears at least 3 times, and give its complexity.

<details><summary>Answer</summary>

```cpp
bool hasTriple(vector<int>& a) {
    unordered_map<int,int> count;
    for (int x : a)
        if (++count[x] >= 3) return true;
    return false;
}
```
n iterations x `operator[]` O(1) average (+ increment/compare O(1)) = O(n) average, O(n^2) worst; space O(n).
</details>

**D2.** A file holds n names. Print the names that appear exactly twice in order of their first appearance. Design + complexity.

<details><summary>Answer</summary>

Pass 1: `unordered_map<string,int>` counts, n x O(1) average. Pass 2: walk the input in order, print a name when `count == 2` and then set its count to 0 (or use a second `unordered_set`) so it is printed once. n x O(1) average. Total O(n) average (O(nL) if L is the name length), space O(n). Iterating the map would lose the order; sorting would be O(n log n).
</details>

**D3.** Maintain the 100 largest transaction amounts seen in a stream of n transactions. Data structure, per-element cost, total?

<details><summary>Answer</summary>

A min-heap of size 100: `priority_queue<int, vector<int>, greater<int> >`. Per transaction: compare with `top()` O(1); if larger, `pop` O(log 100) + `push` O(log 100). Total O(n log 100) = O(n) with a small constant; space O(100) = O(1). In general O(n log k), O(k) space.
</details>

**D4.** Given `set<int> s` (n elements), count how many elements lie in [lo, hi]. Best STL approach and its complexity?

<details><summary>Answer</summary>

`lower_bound(lo)` and `upper_bound(hi)` are O(log n) each, but counting with `std::distance` walks the range: O(m) for m elements, total O(log n + m). The STL `set` has no O(log n) rank query (that needs an order-statistic tree).
</details>

**D5.** True or false (and why): "Replacing `unordered_map` by `map` in the DNA solution changes the correctness but not the complexity."

<details><summary>Answer</summary>

False. The correctness is unchanged; the complexity changes from O(n) average to O(n log n) worst case, since each access is a tree search.
</details>
