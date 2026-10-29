"""Friendly error pages without internal details (01-plan phase 10)."""


def test_500_page_hides_details(app, client, repos):
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.get("/test-crash")
    def crash():
        raise RuntimeError("secret internal detail")

    response = client.get("/test-crash")
    assert response.status_code == 500
    page = response.data.decode()
    assert "Something went wrong" in page
    assert "secret internal detail" not in page and "Traceback" not in page


def test_404_page(client, repos):
    response = client.get("/no-such-page")
    assert response.status_code == 404
    assert "Page not found" in response.data.decode()
