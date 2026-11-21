from django.test import SimpleTestCase, TestCase

from core_app.views import min_bundles, rewatch_order, summarize_rewatch, would_create_cycle

# The brief's example data:
# 1 Iron Man, 2 The First Avenger, 3 The Avengers, 4 Civil War,
# 5 Ragnarok, 6 Infinity War, 7 Endgame, 8 Doomsday
BRIEF = {1: [], 2: [], 3: [1, 2], 4: [3], 5: [], 6: [4, 5], 7: [6], 8: [7]}


def assert_valid_order(test, order, graph):
    """Every movie appears once, and only after all of its prerequisites."""
    test.assertEqual(len(order), len(set(order)), "duplicate movie in order")
    position = {movie: index for index, movie in enumerate(order)}
    for movie in order:
        for prereq in graph[movie]:
            test.assertIn(prereq, position, "prerequisite missing from order")
            test.assertLess(position[prereq], position[movie])


class CycleCheckTests(SimpleTestCase):
    def test_brief_example_endgame_before_iron_man(self):
        self.assertTrue(would_create_cycle(1, [7], BRIEF))

    def test_self_dependency(self):
        self.assertTrue(would_create_cycle(1, [1], BRIEF))

    def test_two_movie_loop(self):
        self.assertTrue(would_create_cycle(3, [4], BRIEF))

    def test_three_movie_loop(self):
        graph = {1: [], 2: [1], 3: [2]}
        self.assertTrue(would_create_cycle(1, [3], graph))

    def test_valid_new_link(self):
        self.assertFalse(would_create_cycle(5, [1], BRIEF))
        self.assertFalse(would_create_cycle(8, [1], BRIEF))

    def test_clearing_prerequisites(self):
        self.assertFalse(would_create_cycle(1, [], BRIEF))


class RewatchOrderTests(SimpleTestCase):
    def test_doomsday_needs_all_seven_others(self):
        order = rewatch_order(8, BRIEF)
        self.assertEqual(set(order), {1, 2, 3, 4, 5, 6, 7})
        assert_valid_order(self, order, BRIEF)

    def test_civil_war(self):
        order = rewatch_order(4, BRIEF)
        self.assertEqual(set(order[:2]), {1, 2})
        self.assertEqual(order[2], 3)
        self.assertEqual(len(order), 3)

    def test_no_prerequisites_gives_empty_list(self):
        self.assertEqual(rewatch_order(5, BRIEF), [])

    def test_target_is_never_included(self):
        for target in BRIEF:
            self.assertNotIn(target, rewatch_order(target, BRIEF))

    def test_diamond_lists_shared_movie_once(self):
        graph = {1: [], 2: [1], 3: [1], 4: [2, 3]}
        order = rewatch_order(4, graph)
        self.assertEqual(sorted(order), [1, 2, 3])
        assert_valid_order(self, order, graph)


class SummaryTests(SimpleTestCase):
    MOVIES = {
        1: {"runtime": 126, "watched": True},
        2: {"runtime": 124, "watched": True},
        3: {"runtime": 143, "watched": True},
        4: {"runtime": 147, "watched": False},
        5: {"runtime": 130, "watched": False},
        6: {"runtime": 149, "watched": False},
        7: {"runtime": 181, "watched": False},
        8: {"runtime": 150, "watched": False},
    }

    def test_doomsday_summary(self):
        result = summarize_rewatch(rewatch_order(8, BRIEF), self.MOVIES)
        self.assertEqual(result["total_count"], 7)
        self.assertEqual(result["watched_count"], 3)
        self.assertEqual(result["remaining_runtime_minutes"], 607)

    def test_empty_list_summary(self):
        result = summarize_rewatch([], self.MOVIES)
        self.assertEqual(result["total_count"], 0)
        self.assertEqual(result["watched_count"], 0)
        self.assertEqual(result["remaining_runtime_minutes"], 0)

    def test_everything_watched(self):
        result = summarize_rewatch(rewatch_order(4, BRIEF), self.MOVIES)
        self.assertEqual(result["watched_count"], 3)
        self.assertEqual(result["remaining_runtime_minutes"], 0)





class BookingTests(SimpleTestCase):
    def test_brief_example_1(self):
        self.assertEqual(min_bundles([1, 3, 4], 6), {3: 2})

    def test_brief_example_2(self):
        self.assertEqual(min_bundles([2, 5], 11), {5: 1, 2: 3})

    def test_brief_example_3(self):
        self.assertEqual(min_bundles([6, 9, 20], 44), {20: 1, 9: 2, 6: 1})

    def test_brief_example_4_not_possible(self):
        self.assertIsNone(min_bundles([4, 6], 7))

    def test_group_of_one(self):
        self.assertEqual(min_bundles([1], 1), {1: 1})

    def test_bundle_bigger_than_group(self):
        self.assertIsNone(min_bundles([500], 3))

    def test_largest_group_size(self):
        self.assertEqual(min_bundles([1, 500], 10000), {500: 20})






class MovieApiTests(TestCase):
    def post_movie(self, title, year, runtime, prerequisites=()):
        response = self.client.post(
            "/api/movies",
            {"title": title, "release_year": year, "runtime": runtime,
             "prerequisites": list(prerequisites)},
            content_type="application/json",
        )
        return response.json()["id"]

    def patch_movie(self, movie_id, data):
        return self.client.patch(
            f"/api/movies/{movie_id}", data, content_type="application/json"
        )

    def rewatch(self, movie_id):
        return self.client.get(f"/api/movies/{movie_id}/rewatch-order")

    def setUp(self):
        # The brief's example data
        self.iron_man = self.post_movie("Iron Man", 2008, 126)
        self.first_avenger = self.post_movie("Captain America: The First Avenger", 2011, 124)
        self.avengers = self.post_movie("The Avengers", 2012, 143, [self.iron_man, self.first_avenger])
        self.civil_war = self.post_movie("Captain America: Civil War", 2016, 147, [self.avengers])
        self.ragnarok = self.post_movie("Thor: Ragnarok", 2017, 130)
        self.infinity_war = self.post_movie("Avengers: Infinity War", 2018, 149, [self.civil_war, self.ragnarok])
        self.endgame = self.post_movie("Avengers: Endgame", 2019, 181, [self.infinity_war])
        self.doomsday = self.post_movie("Avengers: Doomsday", 2026, 150, [self.endgame])

    def test_rewatch_order_for_doomsday(self):
        data = self.rewatch(self.doomsday).json()
        ids = [movie["id"] for movie in data["order"]]
        self.assertEqual(len(ids), 7)
        self.assertNotIn(self.doomsday, ids)
        # every movie comes after its prerequisites
        self.assertLess(ids.index(self.iron_man), ids.index(self.avengers))
        self.assertLess(ids.index(self.first_avenger), ids.index(self.avengers))
        self.assertLess(ids.index(self.avengers), ids.index(self.civil_war))
        self.assertLess(ids.index(self.civil_war), ids.index(self.infinity_war))
        self.assertLess(ids.index(self.ragnarok), ids.index(self.infinity_war))
        self.assertLess(ids.index(self.infinity_war), ids.index(self.endgame))

    def test_rewatch_order_for_civil_war(self):
        ids = [m["id"] for m in self.rewatch(self.civil_war).json()["order"]]
        self.assertEqual(set(ids[:2]), {self.iron_man, self.first_avenger})
        self.assertEqual(ids[2], self.avengers)
        self.assertEqual(len(ids), 3)

    def test_rewatch_order_for_ragnarok_is_empty(self):
        data = self.rewatch(self.ragnarok).json()
        self.assertEqual(data["order"], [])
        self.assertEqual(data["total_count"], 0)

    def test_endgame_as_prerequisite_of_iron_man_is_circular(self):
        response = self.patch_movie(self.iron_man, {"prerequisites": [self.endgame]})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "CIRCULAR_DEPENDENCY")

    def test_movie_cannot_need_itself(self):
        response = self.patch_movie(self.iron_man, {"prerequisites": [self.iron_man]})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "CIRCULAR_DEPENDENCY")

    def test_rejected_update_changes_nothing(self):
        self.patch_movie(self.iron_man, {"prerequisites": [self.endgame]})
        self.assertEqual(self.rewatch(self.iron_man).json()["order"], [])

    def test_duplicate_title_ignoring_case(self):
        response = self.client.post(
            "/api/movies",
            {"title": "iron man", "release_year": 2008, "runtime": 126},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "DUPLICATE_NAME")

    def test_invalid_runtime(self):
        response = self.client.post(
            "/api/movies",
            {"title": "Too Long", "release_year": 2020, "runtime": 500},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "VALIDATION_ERROR")

    def test_watched_changes_summary(self):
        self.patch_movie(self.iron_man, {"watched": True})
        data = self.rewatch(self.doomsday).json()
        self.assertEqual(data["total_count"], 7)
        self.assertEqual(data["watched_count"], 1)
        # the seven runtimes add up to 1000 minutes, minus Iron Man's 126
        self.assertEqual(data["remaining_runtime_minutes"], 874)

    def test_rewatch_unknown_movie(self):
        response = self.rewatch(99999)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "NOT_FOUND")

    def test_duplicate_title_with_extra_spaces(self):
        response = self.client.post(
            "/api/movies",
            {"title": "Iron    Man ", "release_year": 2008, "runtime": 126},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "DUPLICATE_NAME")


class CinemaApiTests(TestCase):
    def make_cinema(self, name, sizes):
        response = self.client.post(
            "/api/cinemas", {"name": name, "bundle_sizes": sizes},
            content_type="application/json",
        )
        return response.json()["id"]

    def booking(self, cinema_id, group_size):
        return self.client.get(f"/api/cinemas/{cinema_id}/booking?groupSize={group_size}")

    def test_brief_example_1(self):
        cinema = self.make_cinema("A", [1, 3, 4])
        data = self.booking(cinema, 6).json()
        self.assertEqual(data["total_bundles"], 2)
        self.assertEqual(data["bundles"], [{"size": 3, "count": 2}])

    def test_brief_example_2(self):
        cinema = self.make_cinema("B", [2, 5])
        data = self.booking(cinema, 11).json()
        self.assertEqual(data["total_bundles"], 4)
        self.assertEqual(data["bundles"], [{"size": 5, "count": 1}, {"size": 2, "count": 3}])

    def test_brief_example_3(self):
        cinema = self.make_cinema("C", [6, 9, 20])
        data = self.booking(cinema, 44).json()
        self.assertEqual(data["total_bundles"], 4)
        self.assertEqual(
            data["bundles"],
            [{"size": 20, "count": 1}, {"size": 9, "count": 2}, {"size": 6, "count": 1}],
        )

    def test_brief_example_4_not_possible(self):
        cinema = self.make_cinema("D", [4, 6])
        response = self.booking(cinema, 7)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["possible"])

    def test_booking_invalid_group_size(self):
        cinema = self.make_cinema("E", [2, 5])
        for bad in ["0", "10001", "abc", "2.5"]:
            self.assertEqual(self.booking(cinema, bad).status_code, 400)
        response = self.client.get(f"/api/cinemas/{cinema}/booking")   # missing groupSize
        self.assertEqual(response.status_code, 400)

    def test_booking_unknown_cinema(self):
        response = self.booking(99999, 6)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "NOT_FOUND")

    def test_duplicate_cinema_name_ignoring_case(self):
        self.make_cinema("Galaxy", [2, 5])
        response = self.client.post(
            "/api/cinemas", {"name": "galaxy", "bundle_sizes": [3]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "DUPLICATE_NAME")

    def test_invalid_bundle_sizes(self):
        bad_lists = [[], list(range(1, 12)), [0], [501], [5, 5]]
        for sizes in bad_lists:
            response = self.client.post(
                "/api/cinemas", {"name": "Bad", "bundle_sizes": sizes},
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 400)
            
    def test_duplicate_cinema_name_with_extra_spaces(self):
        self.make_cinema("Star Hall", [5])
        response = self.client.post(
            "/api/cinemas", {"name": "star    hall", "bundle_sizes": [3]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 409)